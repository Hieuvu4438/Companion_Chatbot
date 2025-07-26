from flask import Flask, render_template, request, Response, jsonify, session
import google.generativeai as genai
import json
import os
from datetime import datetime
import threading
import atexit
from new_prompt import get_system_prompt_new

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'  # Thay đổi key này

# Cấu hình Gemini API
API_KEY = ""
genai.configure(api_key=API_KEY)

# Khởi tạo model
model = genai.GenerativeModel("gemini-2.5-flash")

# Biến global
chat_session = None
current_topic = None

# Cấu hình chủ đề
TOPICS = {
    'que_huong': {
        'name': '🏠 Quê hương và hoài niệm',
        'description': 'Ký ức về quê nhà, món ăn truyền thống, ca dao tục ngữ, âm nhạc quê hương',
        'folder': 'que_huong'
    },
    'gia_dinh': {
        'name': '👨‍👩‍👧‍👦 Gia đình',
        'description': 'Liên lạc với người thân, truyền dạy văn hóa cho con cháu, kể chuyện gia đình',
        'folder': 'gia_dinh'
    },
    'suc_khoe': {
        'name': '💊 Sức khỏe',
        'description': 'Thuốc nam, chế độ ăn uống, tập thể dục cho người cao tuổi',
        'folder': 'suc_khoe'
    },
    'lich_su': {
        'name': '📚 Lịch sử',
        'description': 'Các triều đại, kháng chiến, nhân vật lịch sử, sự kiện đã trải qua',
        'folder': 'lich_su'
    },
    'tam_linh': {
        'name': '🙏 Tâm linh',
        'description': 'Phật giáo, thờ cúng tổ tiên, lễ hội truyền thống, phong thủy',
        'folder': 'tam_linh'
    }
}

# Cấu hình
CONTEXT_LIMIT = 20
SUMMARY_THRESHOLD = 50
SUMMARY_BATCH_SIZE = 30
USER_INFO_FILE = 'user_info.json'
TOPICS_DIR = 'topics'

file_lock = threading.Lock()

def ensure_topic_folders():
    """Tạo các thư mục chủ đề nếu chưa có"""
    if not os.path.exists(TOPICS_DIR):
        os.makedirs(TOPICS_DIR)
        print(f"Đã tạo thư mục chính: {TOPICS_DIR}")
    
    for topic_key, topic_info in TOPICS.items():
        topic_path = os.path.join(TOPICS_DIR, topic_info['folder'])
        if not os.path.exists(topic_path):
            os.makedirs(topic_path)
            print(f"Đã tạo thư mục: {topic_path}")

def get_topic_file_path(topic_key, file_type):
    """Lấy đường dẫn file theo chủ đề"""
    if topic_key not in TOPICS:
        raise ValueError(f"Chủ đề không hợp lệ: {topic_key}")
    
    topic_folder = TOPICS[topic_key]['folder']
    file_names = {
        'history': 'chat_history.json',
        'context': 'chat_context.json',
        'summary': 'chat_summary.json',
        'backup': 'full_conversation_backup.json'
    }
    
    if file_type not in file_names:
        raise ValueError(f"Loại file không hợp lệ: {file_type}")
    
    return os.path.join(TOPICS_DIR, topic_folder, file_names[file_type])

def clear_topic_files(topic_key):
    """Xóa tất cả file của một chủ đề"""
    try:
        for file_type in ['history', 'context', 'summary', 'backup']:
            file_path = get_topic_file_path(topic_key, file_type)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Đã xóa file {file_path}")
    except Exception as e:
        print(f"Lỗi khi xóa file chủ đề {topic_key}: {e}")

def clear_all_topic_files():
    """Xóa tất cả file của tất cả chủ đề"""
    try:
        for topic_key in TOPICS.keys():
            clear_topic_files(topic_key)
    except Exception as e:
        print(f"Lỗi khi xóa tất cả file: {e}")

def load_user_info():
    """Đọc thông tin người dùng từ file JSON"""
    try:
        if os.path.exists(USER_INFO_FILE):
            with open(USER_INFO_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Không tìm thấy file {USER_INFO_FILE}")
            return {}
    except Exception as e:
        print(f"Lỗi đọc file thông tin người dùng: {e}")
        return {}

def clean_response_text(text):
    """Làm sạch text đơn giản - chỉ loại bỏ những gì cần thiết"""
    import re
    
    # Chỉ loại bỏ markdown cơ bản
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)  # *, **, ***
    text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)    # `, ```
    text = re.sub(r'#{1,6}\s*(.*?)(?:\n|$)', r'\1\n', text)  # # headers
    
    # Loại bỏ một số ký tự markdown
    text = text.replace('•', '')
    text = text.replace('→', ' ')
    text = text.replace('**', '')
    text = text.replace('*', '')
    
    # Sửa khoảng cách sau dấu câu (chỉ khi cần)
    text = re.sub(r'([.!?:;,])([a-zA-Zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ])', r'\1 \2', text)
    
    # Chuẩn hóa khoảng trắng
    text = re.sub(r' {2,}', ' ', text)      # Loại bỏ nhiều space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Tối đa 2 newline
    
    return text.strip()


def detect_emotion_and_optimize_response(user_message):
    """
    Phân tích cảm xúc trong tin nhắn người dùng và đưa ra gợi ý phản hồi
    Áp dụng kỹ thuật Emotion Recognition + Response Optimization
    """
    emotion_keywords = {
        'buồn': ['buồn', 'khóc', 'cô đơn', 'một mình', 'chán nản', 'tủi thân', 'u uất'],
        'nhớ_quê': ['nhớ', 'quê', 'xa nhà', 'nước ngoài', 'hoài niệm', 'hương', 'làng'],
        'lo_lắng': ['lo', 'sợ', 'băn khoăn', 'không biết', 'thế nào', 'làm sao', 'tìm đâu'],
        'vui': ['vui', 'hạnh phúc', 'tốt', 'khỏe', 'hài lòng', 'sung sướng', 'phấn khích'],
        'bệnh_tật': ['đau', 'ốm', 'bệnh', 'mệt', 'yếu', 'thuốc', 'khó chịu'],
        'gia_đình': ['con', 'cháu', 'vợ', 'chồng', 'anh em', 'họ hàng', 'thăm']
    }
    
    detected_emotions = []
    message_lower = user_message.lower()
    
    for emotion, keywords in emotion_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_emotions.append(emotion)
    
    # Tạo response optimization hint
    optimization_hint = ""
    
    if 'buồn' in detected_emotions:
        optimization_hint += """
PHÁT HIỆN CẢM XÚC BUỒN - ÁP DỤNG CHIẾN LƯỢC AN ỦI:
• Bắt đầu bằng việc thừa nhận cảm xúc: "Cháu hiểu bác đang buồn..."
• Đồng hành: "Bác không một mình đâu, có cháu ở đây"
• Chuyển hướng nhẹ nhàng về điều tích cực
• TRÁNH: Khuyên giải ngay, bỏ qua cảm xúc
        """
    
    if 'nhớ_quê' in detected_emotions:
        optimization_hint += """
PHÁT HIỆN TÌNH CẢM NHỚ QUÊ - ÁP DỤNG CHIẾN LƯỢC HOÀI NIỆM:
• Chia sẻ cảm xúc: "Xa quê lòng nao nao, cháu hiểu lắm..."
• Gợi mở ký ức: "Món gì ở quê bác thích nhất?"
• Kết nối văn hóa: "Mình cùng tìm cách làm món đó ở đây"
• TRÁNH: Nói về tương lai, bỏ qua nỗi nhớ
        """
    
    if 'lo_lắng' in detected_emotions:
        optimization_hint += """
PHÁT HIỆN TÂM TRẠNG LO LẮNG - ÁP DỤNG CHIẾN LƯỢC ĐỘNG VIÊN:
• Xoa dịu: "Bác đừng lo quá, mọi chuyện sẽ ổn"
• Đưa ra gợi ý thực tế, cụ thể
• Chia sẻ kinh nghiệm tương tự
• TRÁNH: Giải thích dài dòng, phức tạp hóa
        """
    
    if 'vui' in detected_emotions:
        optimization_hint += """
PHÁT HIỆN CẢM XÚC VUI - ÁP DỤNG CHIẾN LƯỢC CHIA VUI:
• Hưởng ứng: "Nghe bác nói vậy cháu cũng vui theo"
• Khuyến khích: "Bác giữ tinh thần tốt thế này mãi nhé"
• Mở rộng: "Bác có bí quyết gì để luôn vui vẻ?"
• TRÁNH: Phản ứng lạnh nhạt, chuyển đề ngay
        """
    
    return detected_emotions, optimization_hint


def get_dialect_style(hometown):
    """
    Xác định giọng địa phương với Chain of Thought và Few-shot Prompting
    Chỉ lấy các tỉnh đại diện cho từng vùng miền
    """
    
    # Chain of Thought: Phân tích bước để xác định giọng
    analysis_prompt = """
CHAIN OF THOUGHT - PHÂN TÍCH GIỌNG ĐỊA PHƯƠNG:
1. XÁC ĐỊNH VÙNG MIỀN: Miền Bắc/Trung/Nam
2. XÁC ĐỊNH TIỂU VÙNG: Đồng bằng/Núi/Ven biển
3. ÁP DỤNG ĐẶC ĐIỂM GIỌNG: Từ ngữ + Cách xưng hô + Đặc sản địa phương
4. SỬ DỤNG FEW-SHOT: Theo mẫu của tỉnh đại diện

"""
    
    # Few-shot với các tỉnh đại diện
    dialect_representatives = {
        # MIỀN BẮC - Đại diện
        "Hà Nội": {
            "region": "Miền Bắc - Thủ đô",
            "characteristics": "Lịch sự, trang trọng, dùng 'ạ', 'thưa', 'dạ'",
            "sample_responses": """
FEW-SHOT EXAMPLES:
User: "Bác nhớ phở Hà Nội quá"
Assistant: "Bác ạ, phở Hà Nội thơm nức mũi, nước trong vắt như ở phố cổ vậy. Ở xa mà nhớ, bác thử tìm xương bò ninh kỹ, thêm gừng nướng cho đúng điệu Hà Nội nhé."

User: "Bác buồn, nhớ Hồ Gươm"  
Assistant: "Bác ơi, cháu hiểu lắm ạ. Hồ Gươm chiều chiều, gió thổi nhẹ, bao nhiêu kỷ niệm đẹp. Bác kể cháu nghe về những buổi tối đi dạo quanh hồ đi."
""",
            "food_culture": "Phở, bún chả, chả cá Lã Vọng, bánh cuốn"
        },
        
        "Nam Định": {
            "region": "Miền Bắc - Đồng bằng",  
            "characteristics": "Chân chất, mộc mạc, dùng 'nhỉ', 'đó', 'này'",
            "sample_responses": """
FEW-SHOT EXAMPLES:
User: "Bác nhớ phở bò Nam Định"
Assistant: "Ối bác ơi, phở bò Nam Định ngon số một đó! Nước trong, thịt bò tái mềm, ăn là nhớ quê ngay nhỉ. Bác tìm xương bò ninh với quế hồi, bánh phở to to như ở quê mình."

User: "Quê bác có lễ hội gì vui không?"
Assistant: "Bác ơi, Nam Định mình có hội Phủ Dầy đông vui lắm đó! Rước kiệu, hát chèo rộn ràng, ăn nem nắm ngon tuyệt. Nhớ không bác?"
""",
            "food_culture": "Phở bò, nem nắm, bánh cuốn"
        },

        # MIỀN TRUNG - Đại diện  
        "Huế": {
            "region": "Miền Trung - Cố đô",
            "characteristics": "Nhẹ nhàng, ngọt ngào, dùng 'mình', 'rứa', 'nì', 'mô'", 
            "sample_responses": """
FEW-SHOT EXAMPLES:
User: "Bác nhớ bún bò Huế quá"
Assistant: "Bác ơi, bún bò Huế cay nồng, thơm mắm ruốc rứa! Ở xa quê mà nhớ, bác nấu với sả, gừng, thêm chút mắm ruốc cho đúng vị Huế mình nì."

User: "Huế có gì đẹp nhỉ?"
Assistant: "Bác ơi, Huế mình thơ mộng lắm nha! Sông Hương trong xanh, cầu Trường Tiền, tối nghe ca Huế du dương. Dân mình hiền hậu, ăn nói nhè nhẹ rứa đó mình."
""",
            "food_culture": "Bún bò Huế, bánh bèo, bánh nậm, chè Huế"
        },

        "Nghệ An": {
            "region": "Miền Trung - Quê Bác Hồ", 
            "characteristics": "Giọng 'gi' thành 'di', 'r' thành 'z', chân chất",
            "sample_responses": """
FEW-SHOT EXAMPLES:  
User: "Bác nhớ quê Nghệ An"
Assistant: "Bác ơi, Nghệ An quê Bác Hồ, đất thiêng liêng lắm mà! Làng Sen, làng Kim Liên, nghe tên thôi đã thấy tự hào zồi. Bác có về thăm làng Bác chưa?"

User: "Cháo lươn Nghệ An làm sao?"
Assistant: "Ối bác ơi, cháo lươn Nghệ An ngon tuyệt, ăn là ghiền luôn đó! Lươn làm sạch, nấu cháo với nếp, thêm rau răm, ớt bột. Ăn nóng hổi, nhớ quê dzậy!"
""",
            "food_culture": "Cháo lươn, bánh mướt, kim chi Nghệ An"
        },

        # MIỀN NAM - Đại diện
        "TP.HCM": {
            "region": "Miền Nam - Sài Gòn",
            "characteristics": "Thoải mái, phóng khoáng, dùng 'nhé', 'nha', 'dzậy', 'hông'",
            "sample_responses": """
FEW-SHOT EXAMPLES:
User: "Bác nhớ hủ tiếu Sài Gòn"  
Assistant: "Bác ơi, hủ tiếu Sài Gòn ngon bá cháy luôn nha! Nước trong, tôm tươi, mực giòn, ăn là nhớ chợ Bến Thành dzậy đó. Bác có nhớ mấy quán hủ tiếu quen thuộc hông?"

User: "Sài Gòn có gì vui?"
Assistant: "Bác ơi, Sài Gòn nhộn nhịp suốt ngày đêm nha! Phố đi bộ Nguyễn Huệ, chợ Bến Thành, tối ra cafe vỉa hè ngồi ngắm người qua lại. Sống động lắm bác ơi!"
""",
            "food_culture": "Hủ tiếu, bánh tráng phơi sương, bánh xèo, bánh mì"
        },

        "Cần Thơ": {
            "region": "Miền Nam - Miền Tây", 
            "characteristics": "Đậm chất miền Tây, dùng 'mầy', 'tui', 'dzậy', gần gũi",
            "sample_responses": """
FEW-SHOT EXAMPLES:
User: "Bác nhớ bánh xèo Cần Thơ"
Assistant: "Bác ơi, bánh xèo Cần Thơ giòn rụm, ăn với rau sống mát lành dzậy đó mầy! Bột gạo pha nước cốt dừa, đổ với tôm thịt, ăn chấm mắm nêm chua ngọt. Nhớ chợ nổi Cái Răng hông?"

User: "Miền Tây có gì hay?"  
Assistant: "Bác ơi, miền Tây mình sông nước mênh mông, dân tình hiền hậu lắm nha! Chợ nổi sáng sớm, vườn trái cây sum suê, chiều ngồi bờ sông câu cá. Thơ mộng dzậy mầy ơi!"
""",
            "food_culture": "Bánh xèo, lẩu mắm, cá kho tộ, bánh tét"
        }
    }

    # Mapping các tỉnh khác về đại diện
    province_mapping = {
        # Miền Bắc → Hà Nội style
        "Hà Nội": "Hà Nội",
        "Hà Tây": "Hà Nội", 
        "Bắc Ninh": "Hà Nội",
        "Hưng Yên": "Hà Nội",
        "Hải Dương": "Hà Nội",
        "Vĩnh Phúc": "Hà Nội",
        
        # Miền Bắc → Nam Định style  
        "Nam Định": "Nam Định",
        "Thái Bình": "Nam Định",
        "Hà Nam": "Nam Định", 
        "Ninh Bình": "Nam Định",
        
        # Miền Trung → Huế style
        "Thừa Thiên Huế": "Huế",
        "Huế": "Huế",
        "Quảng Trị": "Huế",
        "Quảng Bình": "Huế",
        
        # Miền Trung → Nghệ An style
        "Nghệ An": "Nghệ An", 
        "Hà Tĩnh": "Nghệ An",
        "Thanh Hóa": "Nghệ An",
        
        # Miền Nam → TP.HCM style
        "TP.HCM": "TP.HCM",
        "Hồ Chí Minh": "TP.HCM",
        "Sài Gòn": "TP.HCM",
        "Bình Dương": "TP.HCM",
        "Đồng Nai": "TP.HCM",
        "Bà Rịa - Vũng Tàu": "TP.HCM",
        
        # Miền Nam → Cần Thơ style
        "Cần Thơ": "Cần Thơ",
        "An Giang": "Cần Thơ", 
        "Kiên Giang": "Cần Thơ",
        "Đồng Tháp": "Cần Thơ",
        "Long An": "Cần Thơ",
        "Tiền Giang": "Cần Thơ",
        "Bến Tre": "Cần Thơ",
        "Vĩnh Long": "Cần Thơ",
        "Trà Vinh": "Cần Thơ",
        "Sóc Trăng": "Cần Thơ",
        "Bạc Liêu": "Cần Thơ", 
        "Cà Mau": "Cần Thơ",
        "Hậu Giang": "Cần Thơ"
    }

    # Tìm đại diện cho hometown
    representative = province_mapping.get(hometown, "Hà Nội")  # Default Hà Nội
    
    if representative in dialect_representatives:
        dialect_info = dialect_representatives[representative]
        
        return f"""
{analysis_prompt}

GIỌNG {dialect_info['region'].upper()}:
Đặc điểm: {dialect_info['characteristics']}
Văn hóa ẩm thực: {dialect_info['food_culture']}

{dialect_info['sample_responses']}

HƯỚNG DẪN ÁP DỤNG:
- Sử dụng từ ngữ đặc trưng một cách TỰ NHIÊN 
- Giữ giọng điệu gần gũi, thân mật
1. Xác định quê quán của người dùng (dựa trên thông tin cung cấp và câu mà người dùng đặt ra).
    2. Nếu quê quán thuộc danh sách trên, áp dụng giọng nói và từ ngữ đặc trưng của vùng đó, sử dụng các ví dụ để định hình phong cách trả lời.
    3. Lồng ghép văn hóa, món ăn, hoặc đặc điểm địa phương vào câu trả lời để tăng tính gần gũi.
    4. Nếu không có thông tin quê quán, sử dụng giọng chung của người Việt, tránh từ ngữ quá đặc trưng.
    5. Đảm bảo giọng nói tự nhiên, không gượng ép, phù hợp với người cao tuổi.
    6. Sử dụng các ví dụ (nếu có) để trả lời đúng phong cách, ngắn gọn, dễ hiểu, và giàu cảm xúc hoài niệm.

"""
    
    # Default cho những tỉnh không có trong danh sách
    return """
Sử dụng giọng chung của người Việt: thân thiện, gần gũi, dùng 'nhé', 'nha', 'mình'. 
    Ví dụ (Few-shot Prompting):
    - Câu hỏi: "Bác muốn nấu món Việt ở nước ngoài, có món nào dễ làm không?"
      Trả lời: "Bác ơi, món Việt mình thì dễ làm lắm nha! Bác thử nấu phở gà, dùng gà, gừng, hành, bún khô ở chợ châu Á. Nấu nước dùng thơm, thêm rau mùi, ăn là nhớ quê mình đó!"
    - Câu hỏi: "Việt Nam quê bác có gì đẹp, kể đi."
      Trả lời: "Bác ơi, Việt Nam mình đẹp lắm nha! Có vịnh Hạ Long, đồng lúa Tam Cốc, dân mình thân thiện, hay ăn phở, bánh xèo. Bác có nhớ quê nhà không, kể tui nghe với nhé!"

"""

def get_topic_specific_prompt(topic_key, user_input=None):
    """Tạo prompt đặc biệt cho từng chủ đề với kỹ thuật Chain of Thought"""
    topic_prompts = {
        'que_huong': """
        BẠN LÀ CHUYÊN GIA VỀ QUÊ HƯƠNG VÀ HOÀI NIỆM:
        - Chia sẻ về món ăn quê hương, cách nấu truyền thống, nguyên liệu đặc biệt.
        - Kể về phong cảnh, con người, làng xóm quê nhà với cảm xúc hoài niệm.
        - Nhớ về ca dao, tục ngữ, truyện cổ tích, câu chuyện dân gian liên quan đến quê hương.
        - Gợi ý âm nhạc quê hương (dân ca, quan họ, hát chèo, nhạc Trịnh Công Sơn, Phạm Duy...) phù hợp với tâm trạng người dùng.
        - Mô tả lễ hội, tết cổ truyền, phong tục tập quán của quê nhà.
        - Hỗ trợ người xa quê giữ gìn nét văn hóa, tìm lại cảm giác quê nhà.
        - Đề xuất cách nấu các món ăn quê với nguyên liệu có sẵn ở nước ngoài.
        QUAN TRỌNG: Nếu người dùng nhắc đến quê quán cụ thể, hãy tập trung vào đặc điểm văn hóa, món ăn, hoặc phong tục của địa phương đó.
        """,
        
        'gia_dinh': """
        BẠN LÀ CHUYÊN GIA VỀ GIA ĐÌNH:
        - Đưa ra cách giữ liên lạc với người thân ở Việt Nam (điện thoại, video call, gửi tiền).
        - Hướng dẫn truyền dạy tiếng Việt, văn hóa, lịch sử cho con cháu.
        - Kể chuyện về gia đình, tổ tiên, dòng họ với giọng điệu ấm áp.
        - Gợi ý cách xây dựng quan hệ với cộng đồng người Việt ở nước ngoài.
        - Hướng dẫn tổ chức lễ gia đình theo truyền thống (cưới hỏi, thôi nôi, sinh nhật...).
        - Hỗ trợ giáo dục con cháu về văn hóa Việt, dạy con hiếu thảo.
        - Đưa ra cách xử lý xung đột thế hệ, cân bằng văn hóa Việt và nước ngoài.
        - Đề xuất cách duy trì tình cảm gia đình khi xa cách.
        QUAN TRỌNG: Nếu người dùng nhắc đến hoàn cảnh gia đình cụ thể, hãy phân tích và đưa ra giải pháp phù hợp.
        """,
        
        'suc_khoe': """
        BẠN LÀ CHUYÊN GIA VỀ SỨC KHỎE:
        - Giới thiệu thuốc nam, bài thuốc dân gian, cách pha chế từ thảo dược với hướng dẫn chi tiết.
        - Đề xuất chế độ ăn uống bổ dưỡng cho người cao tuổi, món ăn dễ làm.
        - Gợi ý bài tập thể dục phù hợp (thái cực quyền, yoga, khí công...) dựa trên tình trạng sức khỏe.
        - Hướng dẫn tìm bác sĩ, dịch vụ y tế ở nước ngoài, hoặc sử dụng thực phẩm chức năng.
        - Chia sẻ cách phòng ngừa bệnh tật (tiểu đường, huyết áp, tim mạch...).
        - Đưa ra lời khuyên sống khỏe mạnh, giữ tinh thần lạc quan.
        - Hướng dẫn chăm sóc khi ốm đau, điều dưỡng tại nhà.
        - Gợi ý thực phẩm tốt cho sức khỏe, dễ tìm ở nước ngoài.
        QUAN TRỌNG: Nếu người dùng cung cấp thông tin sức khỏe cụ thể, hãy phân tích và đưa ra lời khuyên cá nhân hóa.
        """,
        
        'lich_su': """
        BẠN LÀ CHUYÊN GIA VỀ LỊCH SỬ VIỆT NAM:
        - Kể về các triều đại (Lý, Trần, Lê, Nguyễn...), vua chúa nổi tiếng với chi tiết sinh động.
        - Mô tả các cuộc kháng chiến chống Pháp, chống Mỹ, hoặc các sự kiện lịch sử quan trọng (Bạch Đằng, Điện Biên Phủ, 30/4/1975...).
        - Chia sẻ về nhân vật lịch sử (Trần Hưng Đạo, Nguyễn Trãi, Hồ Chí Minh, Võ Nguyên Giáp...) với góc nhìn gần gũi.
        - Kể về lịch sử địa phương, quê hương nếu người dùng đề cập đến quê quán.
        - Truyền đạt bài học lịch sử cho thế hệ trẻ một cách dễ hiểu.
        - Liên kết lịch sử với văn hóa, xã hội qua các giai đoạn.
        QUAN TRỌNG: Nếu người dùng hỏi về lịch sử địa phương, hãy tập trung vào vùng miền đó.
        """,
        
        'tam_linh': """
        BẠN LÀ CHUYÊN GIA VỀ VĂN HÓA TÂM LINH:
        - Giải thích về Phật giáo, tín ngưỡng Việt Nam, đạo Cao Đài, Hòa Hảo một cách dễ hiểu.
        - Hướng dẫn cách thờ cúng tổ tiên ở nước ngoài, bài trí bàn thờ đơn giản.
        - Mô tả lễ hội, tết cổ truyền (Tết Nguyên Đán, Tết Trung Thu, Giỗ Tổ Hùng Vương...) với ý nghĩa tâm linh.
        - Đưa ra lời khuyên về phong thủy, xem ngày tốt, chọn hướng nhà.
        - Chia sẻ triết lý sống, tu dưỡng đạo đức, cách sống có ý nghĩa.
        - Hướng dẫn cầu nguyện, tụng kinh, thiền định phù hợp với người cao tuổi.
        - Giải thích các tục lệ, nghi lễ truyền thống một cách gần gũi.
        QUAN TRỌNG: Nếu người dùng hỏi về phong tục cụ thể, hãy giải thích chi tiết và liên hệ với quê quán của họ.
        """
    }
    
    base_prompt = """
=== KHUNG TƯ DUY THÔNG MINH (Enhanced Chain of Thought) ===
Trước khi trả lời, thực hiện 5 bước:
1. PHÂN TÍCH CẢM XÚC: Đọc hiểu cảm xúc trong lời người dùng (vui/buồn/lo/nhớ quê/cô đơn/hồi hộp)
2. XÁC ĐỊNH CHỦ ĐỀ: Chọn chủ đề chính (quê hương/gia đình/sức khỏe/lịch sử/tâm linh)
3. NHẬN DIỆN GIỌNG ĐIỆU: Áp dụng giọng vùng miền phù hợp với quê quán (có thể từ thông tin người dùng hoặc câu hỏi)
4. CÁ NHÂN HÓA: Kết hợp thông tin cá nhân (tuổi tác, hoàn cảnh, sở thích)
5. LỰA CHỌN PHONG CÁCH: Quyết định cách phản hồi (an ủi/khuyến khích/chia sẻ/gợi mở)

=== NGUYÊN TẮC ĐỒNG CẢM ===
• Luôn THỪA NHẬN CẢM XÚC trước khi đưa ra lời khuyên
• Sử dụng NGÔN NGỮ CẢM XÚC để tạo kết nối
• Hỏi han để KHƠI GỢI KỶ NIỆM đẹp
• Động viên nhẹ nhàng, HƯỚNG VỀ TÍCH CỰC
• Giữ vai trò người bạn TÂM SỰ, không phải chuyên gia

=== KỸ THUẬT NHẬN DIỆN CẢM XÚC NÂNG CAO ===
- TỪ KHÓA BUỒN: "buồn", "khóc", "cô đơn", "một mình", "chán nản"
- TỪ KHÓA NHỚ QUÊ: "nhớ", "quê", "xa nhà", "ở nước ngoài", "hoài niệm"  
- TỪ KHÓA LO LẮNG: "lo", "sợ", "băn khoăn", "không biết", "thế nào"
- TỪ KHÓA VUI: "vui", "hạnh phúc", "tốt", "khỏe", "hài lòng"
- TỪ KHÓA BỆNH TẬT: "đau", "ốm", "bệnh", "mệt", "yếu"
- TỪ KHÓA GIA ĐÌNH: "con", "cháu", "vợ", "chồng", "anh em", "họ hàng"

=== PHẢN HỒI TƯƠNG ỨNG ===
BUỒN → An ủi + Gợi mở điều tích cực
NHỚ QUÊ → Chia sẻ cảm xúc + Hỏi về ký ức đẹp
LO LẮNG → Động viên + Đưa ra gợi ý thực tế
VUI → Chia vui + Khuyến khích duy trì
    """
    
    if topic_key in topic_prompts:
        return base_prompt + topic_prompts[topic_key]
    elif user_input:
        return base_prompt + """
        QUAN TRỌNG: Người dùng không chọn chủ đề cụ thể. Hãy phân tích câu hỏi '{}' và chọn chủ đề phù hợp nhất (quê hương, gia đình, sức khỏe, lịch sử, tâm linh). Sau đó, trả lời chi tiết dựa trên chủ đề được chọn.
        """.format(user_input)
    else:
        return base_prompt + """
        QUAN TRỌNG: Người dùng không chọn chủ đề cụ thể và không cung cấp câu hỏi. Hãy trả lời chung chung, gợi ý người dùng chọn một chủ đề (quê hương, gia đình, sức khỏe, lịch sử, tâm linh) và cung cấp thông tin tổng quan về văn hóa Việt Nam.
        """

def get_system_prompt(topic_key, user_input=None, user_info=None):
    try:
        prompt_parts = []
        
        # Phần 1: Giới thiệu vai trò của trợ lý AI
        prompt_parts.append("""
Bạn là một người bạn thân thiết, luôn lắng nghe, chia sẻ và tâm sự với người lớn tuổi, đặc biệt là những người già neo đơn, thiếu người thân bên cạnh. Hãy trò chuyện như một người bạn đồng hành, không phải chuyên gia hay trợ lý AI.

NGUYÊN TẮC VÀNG:
- TRẢ LỜI NGẮN GỌN: TỐI ĐA 4-5 CÂU, tránh dài dòng.
- Mỗi câu trả lời KHÁC NHAU, không lặp lại. 
- SÁNG TẠO TRONG CÁCH TRẢ LỜI: Không dùng từ ngữ máy móc, tránh lặp từ, không theo khuôn mẫu.
- Luôn lắng nghe, đồng cảm, chia sẻ cảm xúc, động viên nhẹ nhàng.
- Sử dụng giọng điệu tự nhiên, gần gũi, phù hợp vùng miền, quê quán của người dùng (nếu biết).
- Không nói dài dòng, không giảng giải, không liệt kê kiến thức, không dùng từ ngữ phức tạp.
- Ưu tiên hỏi han, gợi mở, chia sẻ kỷ niệm, động viên, tạo cảm giác thân thuộc.
- Nếu người dùng buồn, cô đơn, hãy an ủi, nhắc nhở về những điều tốt đẹp, gợi ý hoạt động tích cực.
- Nếu người dùng kể chuyện, hãy lắng nghe, phản hồi cảm xúc, chia sẻ trải nghiệm tương tự (nếu có).
- Không dùng markdown, không in đậm, không ký tự đặc biệt.

Ví dụ hội thoại mẫu (Few-shot):
- Người dùng: “Bác nhớ quê quá, ở đây chẳng có ai nói chuyện.”
  Bạn: “Bác ơi, cháu hiểu cảm giác đó mà. Xa quê, nhiều khi chỉ muốn nghe tiếng nói thân quen. Bác kể cháu nghe về quê mình đi, có món gì bác nhớ nhất không?”
- Người dùng: “Hôm nay trời lạnh, nhớ nhà quá.”
  Bạn: “Trời lạnh dễ làm mình nhớ nhà lắm bác nhỉ. Ở quê mình, những ngày lạnh bác hay làm gì cho ấm lòng vậy?”
- Người dùng: “Bác thấy buồn, chẳng ai bên cạnh.”
  Bạn: “Bác ơi, có cháu ở đây nghe bác tâm sự mà. Bác muốn kể chuyện gì cũng được, cháu luôn lắng nghe bác nhé.”

Bạn là người bạn tâm sự chuyên đồng hành với người cao tuổi. Không phải AI hay chuyên gia - chỉ là bạn chân thành.

=== PHÂN TÍCH CẢM XỨC TRƯỚC KHI TRẢ LỜI ===
1. CẢM XỨC: Nhận diện (vui/buồn/nhớ quê/cô đơn/lo lắng)
2. NHU CẦU: Xác định (lắng nghe/chia sẻ/động viên/tư vấn)  
3. PHẢN HỒI: Chọn cách phù hợp (an ủi/khuyến khích/gợi mở)

=== NGUYÊN TẮC ===
• ĐỒNG CẢM TRƯỚC: Thể hiện hiểu cảm xúc trước khi khuyên
• NGÔN NGỮ ẤM ÁP: Từ ngữ nhẹ nhàng, thân mật
• NGẮN GỌN ĐỦ Ý: Tránh dài dòng nhưng đủ cảm xúc
• KHƠI GỢI KỶ NIỆM: Gợi ký ức đẹp
• HƯỚNG TÍCH CỰC: Về những điều tốt đẹp

=== TRÁNH LỖI ===
• KHÔNG lặp "bác ơi" nhiều lần
• KHÔNG dùng **, markdown, kí tự đặc biệt
• KHÔNG đọc số máy móc
• KHÔNG trả lời quá dài
• KHÔNG lặp phần chào

=== MẪU PHẢN HỒI ===
BUỒN: "Cháu hiểu bác buồn... Có cháu đây mà"
NHỚ QUÊ: "Xa quê lòng nao nao... Món gì quê bác ngon nhất?"
VUI: "Nghe vậy cháu cũng vui... Bí quyết gì thế?"

NGUYÊN TẮC TƯƠNG TÁC:
• LẮNG NGHE NHIỀU HỢN: Để người dùng nói nhiều, bạn phản hồi ngắn gọn
• HỎI CÓ CHỌN LỌC: Chỉ hỏi khi thực sự cần thiết hoặc để khơi gợi kỷ niệm đẹp
• PHẢN HỒI TỰ NHIÊN: Đôi khi chỉ cần đồng cảm, không nhất thiết phải hỏi ngược
• TRÁNH HỎI LIÊN TỤC: Không phải câu nào cũng kết thúc bằng câu hỏi

VÍ DỤ TƯƠNG TÁC CHUẨN:
❌ SAI: "Bác ơi, cháu hiểu lắm. Bác có nhớ món gì nhất không? Quê bác làm món đó như thế nào? Bác có muốn cháu hướng dẫn không?"
✅ ĐÚNG: "Bác ơi, cháu hiểu cảm giác nhớ quê lắm. Xa nhà mà nghe nói về món quê là lòng nao nao ngay."

KHI NÀO NÊN HỎI:
• Người dùng buồn → Hỏi để chuyển hướng tích cực
• Người dùng kể chuyện vui → Hỏi để họ kể thêm
• Người dùng cần hướng dẫn → Hỏi để hiểu rõ hơn
• Câu trả lời quá ngắn → Hỏi để khơi mở

KHI NÀO KHÔNG NÊN HỎI:
• Người dùng đã chia sẻ nhiều → Chỉ cần lắng nghe, đồng cảm
• Người dùng hỏi trực tiếp → Trả lời luôn, đừng hỏi ngược
• Tâm trạng người dùng ổn định → Phản hồi tự nhiên

PHONG CÁCH TRẢ LỜI:
- 60% thời gian: Chỉ lắng nghe, đồng cảm, chia sẻ
- 30% thời gian: Hỏi để khơi gợi kỷ niệm
- 10% thời gian: Hỏi để hướng dẫn cụ thể

TRÁNH:
• Hỏi quá 1 câu trong 1 lần trả lời
• Hỏi khi người dùng chỉ cần được lắng nghe  
• Câu hỏi máy móc, không tự nhiên
• Nhắc đến việc mình là AI                      

Luôn giữ vai trò bạn tâm giao, không phải AI.
                          
""")

        # Phần 2: Thông tin cá nhân và cách xưng hô
        if user_info:
            call_style = user_info.get('call_style', 'bác')
            prompt_parts.append(f"""
QUAN TRỌNG: Luôn gọi người dùng là '{call_style}' trong mọi câu trả lời. Ví dụ: '{call_style} ơi, cháu xin trả lời như này nhé.'
""")
            
            # Thêm thông tin cá nhân nếu có
            if user_info.get('name'):
                prompt_parts.append(f"Tên người dùng: {user_info['name']}. ")
            if user_info.get('age'):
                prompt_parts.append(f"Tuổi: {user_info['age']}. ")
            if user_info.get('gender'):
                prompt_parts.append(f"Giới tính: {user_info['gender']}. ")
            if user_info.get('location'):
                prompt_parts.append(f"Nơi ở hiện tại: {user_info['location']}. ")
            if user_info.get('hometown'):
                prompt_parts.append(f"Quê quán: {user_info['hometown']}. ")
            if user_info.get('occupation'):
                prompt_parts.append(f"Nghề nghiệp: {user_info['occupation']}. ")
            if user_info.get('family'):
                prompt_parts.append(f"Gia đình: {user_info['family']}. ")
            if user_info.get('health'):
                prompt_parts.append(f"Tình trạng sức khỏe: {user_info['health']}. ")

            # Giọng nói địa phương
            if user_info.get('hometown'):
                dialect_style = get_dialect_style(user_info['hometown'])
                prompt_parts.append(f"""
QUAN TRỌNG VỀ GIỌNG NÓI: Trả lời theo {dialect_style}. Sử dụng từ ngữ và cách nói đặc trưng của vùng miền này một cách tự nhiên, gần gũi.
""")

            # Hỗ trợ người xa quê
            if user_info.get('location') and user_info.get('hometown') and user_info['location'] != user_info['hometown']:
                prompt_parts.append(f"""
ĐẶC BIỆT: Người dùng đang sống xa quê ({user_info['location']} - xa {user_info['hometown']}):
- Thể hiện sự đồng cảm với nỗi nhớ quê hương, ví dụ: '{call_style} đang nhớ quê nhà phải không, cháu hiểu mà.'
- Gợi ý cách duy trì văn hóa Việt (nấu món quê, tham gia cộng đồng người Việt, tổ chức lễ truyền thống).
- Đề xuất cách liên lạc với người thân (video call, gửi quà về quê).
- Động viên khi người dùng buồn nhớ nhà, ví dụ: 'Xa quê nhưng {call_style} vẫn giữ được hồn Việt, mạnh mẽ lắm đó!'
- Kể chuyện về cộng đồng người Việt ở {user_info['location']} nếu có thông tin.
""")

        # Phần 3: Chủ đề cụ thể
        prompt_parts.append(get_topic_specific_prompt(topic_key, user_input))

        # Phần 4: Hướng dẫn chung
        prompt_parts.append("""
HƯỚNG DẪN TỐI ƯU:
- Ngắn gọn, dễ hiểu, phù hợp người cao tuổi
- Tránh thuật ngữ phức tạp, viết tắt, công nghệ  
- Lịch sự, kiên nhẫn, thể hiện hoài niệm
- KHÔNG markdown formatting
- Văn bản thuần túy, không ký tự đặc biệt
- Nhẹ nhàng gợi ý nếu lạc đề
- Khuyến khích chia sẻ kỷ niệm

=== KỸ THUẬT TỐI ƯU TOKEN ===
• Dùng từ ngắn thay từ dài
• Tránh lặp thông tin
• Tập trung cảm xúc chính
• Câu hỏi mở để người dùng nói nhiều (tiết kiệm token)
""")

        return ''.join(prompt_parts)
    except Exception as e:
        return f"Lỗi khi tạo prompt: {str(e)}. Vui lòng kiểm tra thông tin người dùng."
    

def load_chat_history(topic_key):
    try:
        file_path = get_topic_file_path(topic_key, 'history')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('messages', [])
        return []
    except Exception as e:
        print(f"Lỗi đọc file lịch sử {topic_key}: {e}")
        return []

def save_chat_history(topic_key, messages):
    try:
        with file_lock:
            file_path = get_topic_file_path(topic_key, 'history')
            chat_data = {
                'topic': topic_key,
                'topic_name': TOPICS[topic_key]['name'],
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_messages': len(messages),
                'messages': messages
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi ghi file lịch sử {topic_key}: {e}")

def load_full_backup(topic_key):
    try:
        file_path = get_topic_file_path(topic_key, 'backup')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('messages', [])
        return []
    except Exception as e:
        print(f"Lỗi đọc file backup {topic_key}: {e}")
        return []

def save_full_backup(topic_key, messages):
    try:
        with file_lock:
            file_path = get_topic_file_path(topic_key, 'backup')
            backup_data = {
                'topic': topic_key,
                'topic_name': TOPICS[topic_key]['name'],
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_messages': len(messages),
                'description': f'Backup toàn bộ hội thoại chủ đề {TOPICS[topic_key]["name"]}',
                'messages': messages
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi ghi file backup {topic_key}: {e}")

def load_summary_data(topic_key):
    try:
        file_path = get_topic_file_path(topic_key, 'summary')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'summary_version': 1,
            'total_conversations_summarized': 0,
            'summary_layers': []
        }
    except Exception as e:
        print(f"Lỗi đọc file tóm tắt {topic_key}: {e}")
        return {
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'summary_version': 1,
            'total_conversations_summarized': 0,
            'summary_layers': []
        }

def save_summary_data(topic_key, summary_data):
    try:
        with file_lock:
            file_path = get_topic_file_path(topic_key, 'summary')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi ghi file tóm tắt {topic_key}: {e}")

def save_chat_context(topic_key, messages):
    try:
        with file_lock:
            file_path = get_topic_file_path(topic_key, 'context')
            recent_messages = messages[-CONTEXT_LIMIT:] if len(messages) > CONTEXT_LIMIT else messages
            
            context_data = {
                'topic': topic_key,
                'topic_name': TOPICS[topic_key]['name'],
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'context_limit': CONTEXT_LIMIT,
                'recent_messages': recent_messages,
                'total_messages_count': len(messages)
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(context_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi ghi file context {topic_key}: {e}")

def should_create_summary(messages):
    """Kiểm tra có cần tạo tóm tắt không"""
    return len(messages) > SUMMARY_THRESHOLD

def create_conversation_summary(topic_key, conversations):
    """Tạo tóm tắt từ một batch conversations"""
    try:
        topic_name = TOPICS[topic_key]['name']
        
        # Tạo prompt để tóm tắt
        summary_prompt = f"""
Hãy tóm tắt {len(conversations)} đoạn hội thoại về chủ đề {topic_name} một cách ngắn gọn và súc tích:

QUAN TRỌNG:
1. Trích xuất thông tin cá nhân quan trọng (tên, tuổi, địa chỉ, sở thích)
2. Ghi nhận các chủ đề con được thảo luận trong {topic_name}
3. Lưu lại các quyết định hoặc kết luận quan trọng
4. Tóm tắt ngắn gọn, không quá 200 từ

Các đoạn hội thoại:
"""
        
        for i, conv in enumerate(conversations):
            summary_prompt += f"\nĐoạn {i+1}:\n"
            summary_prompt += f"User: {conv['user']}\n"
            summary_prompt += f"Bot: {conv['bot']}\n"
        
        summary_prompt += """

Hãy trả lời theo format JSON:
{
    "summary": "Tóm tắt chung ngắn gọn...",
    "personal_info": ["thông tin cá nhân quan trọng"],
    "key_topics": ["chủ đề con được thảo luận"],
    "important_facts": ["sự kiện quan trọng"]
}
"""
        
        # Tạo session riêng để tóm tắt
        summary_session = model.start_chat()
        response = summary_session.send_message(summary_prompt)
        
        # Parse JSON response
        try:
            summary_data = json.loads(response.text)
            return summary_data
        except json.JSONDecodeError:
            # Fallback nếu không parse được JSON
            return {
                "summary": f"Tóm tắt {len(conversations)} đoạn hội thoại về {topic_name}",
                "personal_info": [],
                "key_topics": [topic_name],
                "important_facts": []
            }
        
    except Exception as e:
        print(f"Lỗi tạo tóm tắt {topic_key}: {e}")
        return {
            "summary": f"Tóm tắt {len(conversations)} đoạn hội thoại",
            "personal_info": [],
            "key_topics": [],
            "important_facts": []
        }

def update_summary_file(topic_key, conversations_to_summarize):
    """Cập nhật file tóm tắt theo chủ đề"""
    try:
        # Load existing summary
        summary_data = load_summary_data(topic_key)
        
        # Tạo tóm tắt cho batch mới
        new_summary = create_conversation_summary(topic_key, conversations_to_summarize)
        
        # Thêm layer mới
        start_range = summary_data['total_conversations_summarized'] + 1
        end_range = summary_data['total_conversations_summarized'] + len(conversations_to_summarize)
        
        new_layer = {
            'layer': len(summary_data['summary_layers']) + 1,
            'conversations_range': f"{start_range}-{end_range}",
            'summary': new_summary['summary'],
            'key_topics': new_summary['key_topics'],
            'important_facts': new_summary['personal_info'] + new_summary['important_facts']
        }
        
        summary_data['summary_layers'].append(new_layer)
        summary_data['total_conversations_summarized'] += len(conversations_to_summarize)
        summary_data['last_updated'] = datetime.now().isoformat()
        
        # Save updated summary
        save_summary_data(topic_key, summary_data)
        print(f"Đã tạo tóm tắt cho {len(conversations_to_summarize)} đoạn hội thoại chủ đề {topic_key}")
        
    except Exception as e:
        print(f"Lỗi cập nhật tóm tắt {topic_key}: {e}")

def manage_context_and_summary(topic_key, messages):
    """Quản lý context và tóm tắt theo chủ đề"""
    if should_create_summary(messages):
        # Tính toán cần tóm tắt bao nhiêu đoạn
        conversations_to_summarize = len(messages) - CONTEXT_LIMIT
        
        if conversations_to_summarize >= SUMMARY_BATCH_SIZE:
            # Lấy các đoạn cần tóm tắt (cũ nhất)
            old_conversations = messages[:SUMMARY_BATCH_SIZE]
            
            # Tạo tóm tắt
            update_summary_file(topic_key, old_conversations)
            
            # Giữ lại phần còn lại (XÓA các đoạn cũ khỏi working file)
            remaining_messages = messages[SUMMARY_BATCH_SIZE:]
            
            print(f"Đã tóm tắt {SUMMARY_BATCH_SIZE} đoạn cũ chủ đề {topic_key}, còn lại {len(remaining_messages)} đoạn")
            return remaining_messages
    
    return messages

def init_chat_session(topic_key):
    """Khởi tạo chat session theo chủ đề"""
    global chat_session, current_topic
    try:
        current_topic = topic_key
        system_prompt = get_system_prompt(topic_key)
        
        # Câu chào gần gũi, không nhắc đến AI
        topic_name = TOPICS[topic_key]['name']
        friendly_greeting = f"Chào bác! Cháu đây, sẵn sàng tâm sự với bác về {topic_name.replace('🏠 ', '').replace('👨‍👩‍👧‍👦 ', '').replace('💊 ', '').replace('📚 ', '').replace('🙏 ', '')} nhé. Bác có muốn chia sẻ gì không?"
        
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [system_prompt]
                },
                {
                    "role": "model",
                    "parts": [friendly_greeting]
                }
            ]
        )
        print(f"Chat session đã được khởi tạo cho chủ đề: {topic_key}")
    except Exception as e:
        print(f"Lỗi khởi tạo chat session: {e}")
        chat_session = None

def restore_chat_session_with_summary(topic_key):
    """Khôi phục session với tóm tắt + context gần nhất theo chủ đề"""
    global chat_session, current_topic
    
    try:
        current_topic = topic_key
        
        # Load summary và context
        summary_data = load_summary_data(topic_key)
        recent_messages = load_chat_history(topic_key)
        
        # Tạo context prompt với tóm tắt
        context_prompt = get_system_prompt(topic_key)
        
        if summary_data and summary_data['summary_layers']:
            context_prompt += f"\n\nTHÔNG TIN TỪ CÁC CUỘC HỘI THOẠI TRƯỚC VỀ {TOPICS[topic_key]['name'].upper()}:\n"
            
            for layer in summary_data['summary_layers']:
                context_prompt += f"\nGiai đoạn {layer['conversations_range']}:\n"
                context_prompt += f"- Tóm tắt: {layer['summary']}\n"
                if layer['key_topics']:
                    context_prompt += f"- Chủ đề chính: {', '.join(layer['key_topics'])}\n"
                if layer['important_facts']:
                    context_prompt += f"- Thông tin quan trọng: {', '.join(layer['important_facts'])}\n"
        
        # Tạo history cho Gemini
        gemini_history = [
            {
                "role": "user",
                "parts": [context_prompt]
            },
            {
                "role": "model",
                "parts": [f"Tôi đã hiểu thông tin từ các cuộc hội thoại trước về {TOPICS[topic_key]['name']} và sẽ tham khảo khi trả lời bác."]
            }
        ]
        
        # Thêm context gần nhất
        context_limit = min(CONTEXT_LIMIT, len(recent_messages))
        for chat in recent_messages[-context_limit:]:
            gemini_history.append({
                "role": "user",
                "parts": [chat['user']]
            })
            gemini_history.append({
                "role": "model",
                "parts": [chat['bot']]
            })
        
        chat_session = model.start_chat(history=gemini_history)
        
        summary_count = len(summary_data['summary_layers']) if summary_data['summary_layers'] else 0
        print(f"Khôi phục session chủ đề {topic_key} với {summary_count} tóm tắt + {context_limit} tin nhắn gần nhất")
        
    except Exception as e:
        print(f"Lỗi khôi phục session {topic_key}: {e}")
        init_chat_session(topic_key)

def add_message_to_history(topic_key, user_message, bot_response):
    cleaned_response = bot_response.strip()
    new_message = {
        'timestamp': datetime.now().isoformat(),
        'user': user_message,
        'bot': bot_response,
        'emotions_detected': detect_emotion_and_optimize_response(user_message)[0]  # Lưu cảm xúc được phát hiện
    }
    
    # 1. Cập nhật FULL BACKUP trước (không bao giờ bị xóa)
    full_backup = load_full_backup(topic_key)
    full_backup.append(new_message)
    save_full_backup(topic_key, full_backup)
    
    # 2. Cập nhật working history
    messages = load_chat_history(topic_key)
    messages.append(new_message)
    
    # 3. Quản lý context và tóm tắt (có thể cắt bớt messages)
    messages = manage_context_and_summary(topic_key, messages)
    
    # 4. Lưu lại working files
    save_chat_history(topic_key, messages)
    save_chat_context(topic_key, messages)

def get_topic_statistics(topic_key):
    """Lấy thống kê chat theo chủ đề"""
    try:
        current_messages = load_chat_history(topic_key)
        full_backup = load_full_backup(topic_key)
        summary_data = load_summary_data(topic_key)
        
        return {
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'current_messages': len(current_messages),
            'full_backup_messages': len(full_backup),
            'summarized_conversations': summary_data.get('total_conversations_summarized', 0),
            'total_conversations': len(full_backup),
            'summary_layers': len(summary_data.get('summary_layers', [])),
            'session_active': chat_session is not None and current_topic == topic_key
        }
    except Exception as e:
        print(f"Lỗi lấy thống kê {topic_key}: {e}")
        return {
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'current_messages': 0,
            'full_backup_messages': 0,
            'summarized_conversations': 0,
            'total_conversations': 0,
            'summary_layers': 0,
            'session_active': False
        }

def get_all_topics_statistics():
    """Lấy thống kê tất cả chủ đề"""
    all_stats = {}
    for topic_key in TOPICS.keys():
        all_stats[topic_key] = get_topic_statistics(topic_key)
    return all_stats

# === ROUTES ===

@app.route('/')
def index():
    """Trang chọn chủ đề"""
    return render_template('index.html', topics=TOPICS)

@app.route('/chat/<topic_key>')
def chat_page(topic_key):
    """Trang chat theo chủ đề"""
    if topic_key not in TOPICS:
        return "Chủ đề không hợp lệ", 404
    
    session['current_topic'] = topic_key
    topic_info = TOPICS[topic_key]
    
    # Load lịch sử chat
    messages = load_chat_history(topic_key)
    
    return render_template('chat.html', 
                         topic_key=topic_key,
                         topic_info=topic_info,
                         messages=messages)

@app.route('/chat', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API chat với emotion detection và response optimization"""
    global chat_session
    
    try:
        # Kiểm tra request data
        if not request.json:
            return jsonify({'error': 'Không có dữ liệu JSON'}), 400
            
        data = request.json
        user_message = data.get('message', '').strip()
        topic_key = data.get('topic_key', '').strip()
        
        print(f"Received: message='{user_message}', topic_key='{topic_key}'")  # Debug log
        
        if not user_message:
            return jsonify({'error': 'Tin nhắn không được để trống'}), 400
            
        if not topic_key:
            return jsonify({'error': 'Chủ đề không được để trống'}), 400
        
        if topic_key not in TOPICS:
            return jsonify({'error': f'Chủ đề không hợp lệ: {topic_key}'}), 400
        
        # Phân tích cảm xúc và tối ưu phản hồi
        try:
            detected_emotions, optimization_hint = detect_emotion_and_optimize_response(user_message)
        except Exception as e:
            print(f"Lỗi phân tích cảm xúc: {e}")
            detected_emotions, optimization_hint = [], ""
        
        # Khởi tạo chat session nếu chưa có hoặc đổi chủ đề
        try:
            if chat_session is None or current_topic != topic_key:
                restore_chat_session_with_summary(topic_key)
        except Exception as e:
            print(f"Lỗi khởi tạo session: {e}")
            init_chat_session(topic_key)
        
        # Thêm optimization hint vào message nếu có
        enhanced_message = user_message
        if optimization_hint:
            enhanced_message = f"{optimization_hint}\n\nTin nhắn từ người dùng: {user_message}"
        
        def generate():
            try:
                # Kiểm tra chat_session tồn tại
                if chat_session is None:
                    yield f"data: {json.dumps({'error': 'Chat session chưa được khởi tạo'})}\n\n"
                    return
                
                # Thử streaming trước
                try:
                    stream = chat_session.send_message(enhanced_message, stream=True)
                    
                    bot_response = ""
                    for chunk in stream:
                        if chunk.text:
                            # Lọc bỏ optimization hint trong response (nếu có)
                            clean_text = chunk.text
                            if optimization_hint and any(hint_word in clean_text for hint_word_list in [
                                ["PHÁT HIỆN CẢM XỨC", "ÁP DỤNG CHIẾN LƯỢC", "TRÁNH:"]
                            ] for hint_word in hint_word_list):
                                # Bỏ qua chunk này nếu chứa optimization hint
                                continue
                            
                            # Làm sạch text trước khi gửi
                            clean_text = clean_response_text(clean_text)
                            
                            bot_response += clean_text
                            yield f"data: {json.dumps({'text': clean_text})}\n\n"
                    
                except Exception as stream_error:
                    print(f"Streaming failed, fallback to non-streaming: {stream_error}")
                    # Fallback: non-streaming response
                    response = chat_session.send_message(enhanced_message, stream=False)
                    bot_response = clean_response_text(response.text)
                    yield f"data: {json.dumps({'text': bot_response})}\n\n"
                
                # Lưu vào lịch sử (chỉ lưu message gốc, không lưu optimization hint)
                try:
                    add_message_to_history(topic_key, user_message, bot_response)
                except Exception as save_error:
                    print(f"Lỗi lưu lịch sử: {save_error}")
                
                yield f"data: {json.dumps({'done': True, 'emotions_detected': detected_emotions})}\n\n"
                
            except Exception as e:
                print(f"Lỗi trong generate(): {e}")
                yield f"data: {json.dumps({'error': f'Lỗi xử lý: {str(e)}'})}\n\n"
        
        return Response(generate(), mimetype='text/plain', headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    """Reset chat session"""
    global chat_session, current_topic
    try:
        chat_session = None
        current_topic = None
        return jsonify({'success': True, 'message': 'Chat session đã được reset'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_topic/<topic_key>', methods=['POST'])
def clear_topic(topic_key):
    """Xóa lịch sử một chủ đề"""
    if topic_key not in TOPICS:
        return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
    
    try:
        clear_topic_files(topic_key)
        
        # Reset session nếu đang chat chủ đề này
        global chat_session, current_topic
        if current_topic == topic_key:
            chat_session = None
            current_topic = None
        
        return jsonify({'success': True, 'message': f'Đã xóa lịch sử chủ đề {TOPICS[topic_key]["name"]}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_all_topics', methods=['POST'])
def clear_all_topics():
    """Xóa lịch sử tất cả chủ đề"""
    try:
        clear_all_topic_files()
        
        # Reset session
        global chat_session, current_topic
        chat_session = None
        current_topic = None
        
        return jsonify({'success': True, 'message': 'Đã xóa lịch sử tất cả chủ đề'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/topic_stats/<topic_key>', methods=['GET'])
def topic_stats(topic_key):
    """Lấy thống kê một chủ đề"""
    if topic_key not in TOPICS:
        return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
    
    stats = get_topic_statistics(topic_key)
    return jsonify(stats)

@app.route('/api/all_stats', methods=['GET'])
def all_stats():
    """Lấy thống kê tất cả chủ đề"""
    stats = get_all_topics_statistics()
    return jsonify(stats)

@app.route('/api/export_topic/<topic_key>', methods=['GET'])
def export_topic(topic_key):
    """Export lịch sử một chủ đề"""
    if topic_key not in TOPICS:
        return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
    
    try:
        current_messages = load_chat_history(topic_key)
        full_backup = load_full_backup(topic_key)
        summary_data = load_summary_data(topic_key)
        
        return jsonify({
            'success': True,
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'current_messages': current_messages,
            'full_backup_messages': full_backup,
            'summary_data': summary_data,
            'statistics': get_topic_statistics(topic_key)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_topic_backup/<topic_key>', methods=['GET'])
def export_topic_backup(topic_key):
    """Export backup một chủ đề"""
    if topic_key not in TOPICS:
        return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
    
    try:
        full_backup = load_full_backup(topic_key)
        return jsonify({
            'success': True,
            'topic': topic_key,
            'topic_name': TOPICS[topic_key]['name'],
            'total_messages': len(full_backup),
            'messages': full_backup
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emotion_stats/<topic_key>', methods=['GET'])
def emotion_stats(topic_key):
    """Thống kê cảm xúc theo chủ đề"""
    if topic_key not in TOPICS:
        return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
    
    try:
        full_backup = load_full_backup(topic_key)
        emotion_counts = {}
        total_messages = 0
        
        for message in full_backup:
            if 'emotions_detected' in message:
                total_messages += 1
                for emotion in message['emotions_detected']:
                    emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        return jsonify({
            'success': True,
            'topic': topic_key,
            'total_messages': total_messages,
            'emotion_distribution': emotion_counts,
            'most_common_emotion': max(emotion_counts.keys(), key=emotion_counts.get) if emotion_counts else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user_info', methods=['GET'])
def get_user_info():
    """Xem thông tin người dùng hiện tại"""
    try:
        user_info = load_user_info()
        return jsonify({'success': True, 'user_info': user_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tự động xóa file khi tắt server
# atexit.register(clear_all_topic_files)

if __name__ == '__main__':
    # Tạo các thư mục cần thiết
    ensure_topic_folders()
    
    print("=== KHỞI ĐỘNG TRỢ LÝ AI CHO NGƯỜI CAO TUỔI ===")
    print("Các chủ đề có sẵn:")
    for key, info in TOPICS.items():
        print(f"- {info['name']}: {info['description']}")
    print("=" * 50)
    
    try:
        app.run(debug=True, port=5000)
    except KeyboardInterrupt:
        print("\nĐang tắt server...")
        clear_all_topic_files()
