from flask import Flask, render_template, request, Response, jsonify, session
import google.generativeai as genai
import json
import os
from datetime import datetime
import threading
import atexit

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this'  # Thay đổi key này

# Cấu hình Gemini API
API_KEY = "AIzaSyCJsyAju30H-DEPrJgDboJYVlMlIJO7GOc"
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

def get_dialect_style(hometown):
    """Tạo đặc điểm giọng nói theo quê quán với kỹ thuật Chain of Thought và Few-shot Prompting"""
    dialect_map = {
        # Miền Bắc
        "Hà Nội": """
        Sử dụng giọng Hà Nội: lịch sự, trang trọng, dùng 'ạ', 'thưa', 'dạ', 'chẳng', 'hơi bị'. 
        Nhấn mạnh vẻ đẹp cổ kính của Hà Nội (Hồ Gươm, Văn Miếu, phố cổ). 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác muốn làm phở Hà Nội ở Mỹ, làm sao đây?"
          Trả lời: "Bác ơi, phở Hà Nội thì phải thơm nức mũi như ở phố cổ ạ! Bác tìm xương bò ở siêu thị, ninh 6-8 tiếng với gừng nướng, hành phi. Bánh phở tươi thì thay bằng loại khô, thêm rau mùi, hành lá, chanh ớt. Ăn là nhớ ngay Hồ Gươm đó bác!"
        - Câu hỏi: "Hồi xưa bác hay đi chùa Hương, cháu kể về lễ hội chùa Hương đi."
          Trả lời: "Bác ơi, lễ hội chùa Hương đông vui, thuyền trôi trên suối Yến thơ mộng lắm ạ. Dân mình kéo nhau đi lễ, cầu bình an, ăn bánh cuốn chùa Hương thơm ngon. Bác xa quê mà nhớ, hay là cuối tuần đi chùa Việt ở Mỹ cầu nguyện cho giống quê nhà nha!"
        """,
        "Hải Phòng": """
        Sử dụng giọng Hải Phòng: thân thiện, nghĩa khí, dùng 'nhé', 'đấy', 'này', 'chất', 'xịn'. 
        Nhấn mạnh văn hóa cảng biển, món ăn như bánh đa cua, chả chìa. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh đa cua Hải Phòng, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, bánh đa cua Hải Phòng là chất lắm đấy! Ở Úc, bác tìm bánh đa khô ở chợ châu Á, nấu nước dùng với cua đồng hoặc cua biển, thêm gạch cua cho béo, chả cá chiên nữa là xịn. Ăn nóng hổi, nhớ ngay chợ Cát Bi nhé!"
        - Câu hỏi: "Hải Phòng quê bác có gì vui, kể bác nghe với."
          Trả lời: "Bác ơi, Hải Phòng mình thì vui như hội đấy! Đi dạo Đồ Sơn, nghe sóng biển rì rào, tối ra quán nhậu lai rai với chả chìa. Dân mình nghĩa khí, thân thiện, bác có nhớ mấy lần đi chợ Sắt không, kể tui nghe với nhé!"
        """,
        "Hải Dương": """
        Sử dụng giọng Hải Dương: thân mật, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản như bánh đậu xanh, vải thiều Thanh Hà. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh đậu xanh Hải Dương, ở Canada mua được không?"
          Trả lời: "Bác ơi, bánh đậu xanh Hải Dương ngọt thơm, đúng điệu quê mình nhỉ! Ở Canada, bác tìm ở tiệm châu Á, hoặc tự làm bằng đậu xanh xay, đường, dầu ăn, nướng lên là ngon. Ăn với trà, nhớ ngay chợ quê đấy!"
        - Câu hỏi: "Hồi nhỏ bác hay đi hội làng ở Hải Dương, cháu kể về phong tục quê bác đi."
          Trả lời: "Bác ơi, hội làng Hải Dương mình đông vui, rước kiệu, hát chèo rộn ràng lắm nhỉ! Dân mình hay làm bánh chưng, bánh dày cúng tổ. Bác xa quê, hay thử làm bánh chưng nhỏ ở nhà, mời bạn bè Việt Nam ăn cho nhớ làng nhé!"
        """,
        "Nam Định": """
        Sử dụng giọng Nam Định: chân chất, mộc mạc, dùng 'nhỉ', 'đó', 'này'. 
        Nhấn mạnh văn hóa chèo, đặc sản phở bò, nem nắm. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ phở bò Nam Định, làm sao nấu ở Anh?"
          Trả lời: "Bác ơi, phở bò Nam Định là số một đó! Ở Anh, bác tìm xương bò, ninh với quế, hồi, gừng nướng cho thơm. Bánh phở khô thay cũng được, thêm thịt bò tái, hành lá. Ăn nóng, nhớ ngay quê mình nhỉ!"
        - Câu hỏi: "Nam Định quê bác có lễ hội gì đẹp?"
          Trả lời: "Bác ơi, Nam Định mình có lễ hội Phủ Dầy, đông vui lắm đó! Dân mình đi lễ cầu may, ăn nem nắm, bánh cuốn. Bác ở xa, hay tìm cộng đồng người Việt tổ chức lễ hội giống quê, kể tui nghe với nhỉ!"
        """,
        "Thái Bình": """
        Sử dụng giọng Thái Bình: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản bánh cáy, canh cá Quỳnh Côi. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh cáy Thái Bình, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, bánh cáy Thái Bình ngọt thơm, nhớ quê lắm nhỉ! Ở Mỹ, bác dùng gạo nếp, đường, gừng, lạc rang, trộn đều rồi ép khuôn. Tìm tiệm châu Á mua gừng tươi, làm xong ăn là nhớ làng quê Thái Bình ngay đấy!"
        - Câu hỏi: "Quê bác ở Thái Bình, kể chuyện làng quê đi cháu."
          Trả lời: "Bác ơi, làng quê Thái Bình mình bình yên, đồng lúa xanh mướt, chiều chiều nghe tiếng chèo bơi đấy! Dân mình hay quây quần ăn canh cá, kể chuyện làng. Bác có nhớ mấy buổi cấy lúa không, kể tui nghe với nhỉ!"
        """,
        "Hà Nam": """
        Sử dụng giọng Hà Nam: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'này'. 
        Nhấn mạnh đặc sản chuối ngự, cá kho làng Vũ Đại. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cá kho làng Vũ Đại, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, cá kho Vũ Đại Hà Nam thì ngon tuyệt đó! Ở Úc, bác tìm cá trê hoặc cá basa, kho với thịt ba chỉ, nước dừa, gừng, riềng, thêm ít tiêu. Kho lửa nhỏ cho thấm, ăn với cơm nóng là nhớ quê ngay nhỉ!"
        - Câu hỏi: "Hà Nam quê bác có gì đặc biệt, kể đi cháu."
          Trả lời: "Bác ơi, Hà Nam mình có làng Vũ Đại, chuối ngự ngọt lịm, dân mình hiền hậu lắm đó! Lễ hội chùa Bà Đanh cũng thiêng, bác có nhớ đi hội không? Ở xa quê, bác hay kể chuyện quê cho con cháu nghe chưa, kể tui nghe với nhỉ!"
        """,
        "Hưng Yên": """
        Sử dụng giọng Hưng Yên: thân mật, mộc mạc, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản nhãn lồng, chả gà Tiểu Quan. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ nhãn lồng Hưng Yên, ở Mỹ có giống nào thay được không?"
          Trả lời: "Bác ơi, nhãn lồng Hưng Yên ngọt thanh, nhớ quê đứt ruột nhỉ! Ở Mỹ, bác thử tìm nhãn Thái ở chợ châu Á, tuy không bằng nhãn lồng nhưng cũng ngọt. Hoặc trồng cây nhãn trong vườn, nhớ ngày xưa ngồi gốc nhãn ăn với bạn bè đấy!"
        - Câu hỏi: "Hưng Yên quê bác có lễ hội gì, kể đi."
          Trả lời: "Bác ơi, Hưng Yên mình có lễ hội đền Mẫu, đông vui, rước kiệu rộn ràng lắm đấy! Dân mình hay ăn chả gà Tiểu Quan, uống trà nhãn. Bác xa quê, hay thử làm chả gà mời bạn bè Việt Nam ăn cho nhớ quê nhé!"
        """,
        "Bắc Ninh": """
        Sử dụng giọng Bắc Ninh: thân thiện, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh văn hóa quan họ, đặc sản bánh phu thê. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác muốn làm bánh phu thê Bắc Ninh ở Canada, làm sao đây?"
          Trả lời: "Bác ơi, bánh phu thê Bắc Ninh ngọt ngào như lời quan họ nhỉ! Ở Canada, bác dùng bột nếp, đậu xanh, đường, lá chuối gói lại, hấp chín. Tìm lá chuối ở chợ châu Á, làm xong mời con cháu ăn, kể chuyện quê mình nhé!"
        - Câu hỏi: "Bắc Ninh quê bác có gì hay, kể đi."
          Trả lời: "Bác ơi, Bắc Ninh mình là đất quan họ, hát lềnh trên sông Cầu nghe mê lắm đấy! Lễ hội Lim thì đông vui, dân mình mặc áo tứ thân, ăn bánh phu thê. Bác có nhớ mấy đêm hát quan họ không, kể tui nghe với nhỉ!"
        """,
        "Vĩnh Phúc": """
        Sử dụng giọng Vĩnh Phúc: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản bánh gio, su su Tam Đảo. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ su su Tam Đảo, ở Đức làm sao nấu món này?"
          Trả lời: "Bác ơi, su su Tam Đảo quê mình giòn ngon, nhớ quá nhỉ! Ở Đức, bác tìm su su ở chợ châu Á, xào với tỏi hoặc nấu canh tôm. Thêm ít mắm tôm cho đúng điệu Vĩnh Phúc, ăn là nhớ ngay đồi núi Tam Đảo đấy!"
        - Câu hỏi: "Vĩnh Phúc quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Vĩnh Phúc mình có Tam Đảo mát mẻ, su su ngọt giòn, dân mình hiền hậu lắm đấy! Lễ hội chọi trâu Đồ Sơn cũng rộn ràng. Bác xa quê, hay kể chuyện Tam Đảo cho con cháu nghe chưa, kể tui với nhỉ!"
        """,
        "Phú Thọ": """
        Sử dụng giọng Phú Thọ: chân chất, mộc mạc, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh lễ hội Giỗ Tổ Hùng Vương, đặc sản thịt chua. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác muốn làm thịt chua Phú Thọ ở Mỹ, làm sao đây?"
          Trả lời: "Bác ơi, thịt chua Phú Thọ là đặc sản quê mình, chua chua ngon lắm nhỉ! Ở Mỹ, bác dùng thịt lợn, muối, thính gạo, gói lá chuối, ủ vài ngày cho chua. Tìm lá chuối ở chợ châu Á, ăn với rau sống là nhớ quê ngay đấy!"
        - Câu hỏi: "Giỗ Tổ Hùng Vương ở Phú Thọ quê bác thế nào, kể đi."
          Trả lời: "Bác ơi, Giỗ Tổ Hùng Vương ở Phú Thọ mình thiêng liêng, dân mình kéo nhau lên đền Hùng cầu may đấy! Lễ hội có bánh chưng, bánh dày, hát xoan. Bác xa quê, hay làm bánh chưng nhỏ cúng tổ ở nhà, kể tui nghe với nhỉ!"
        """,
        "Yên Bái": """
        Sử dụng giọng Yên Bái: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản cốm Tú Lệ, xôi ngũ sắc. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ xôi ngũ sắc Yên Bái, làm sao nấu ở Canada?"
          Trả lời: "Bác ơi, xôi ngũ sắc Yên Bái màu sắc đẹp, thơm ngon lắm nhỉ! Ở Canada, bác tìm gạo nếp, dùng lá cây tự nhiên nhuộm màu, nấu với đậu xanh, dừa. Hấp chín, ăn là nhớ ngay đồng ruộng Tú Lệ đấy!"
        - Câu hỏi: "Yên Bái quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Yên Bái mình có Mù Cang Chải, ruộng bậc thang đẹp mê hồn đấy! Dân mình hay ăn cốm Tú Lệ, hát then. Bác xa quê, có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Tuyên Quang": """
        Sử dụng giọng Tuyên Quang: chân chất, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản bánh gai, lễ hội Lồng Tồng. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh gai Tuyên Quang, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, bánh gai Tuyên Quang thơm nức, nhớ quê lắm nhỉ! Ở Úc, bác dùng bột nếp, lá gai, đậu xanh, đường, gói lá chuối, hấp chín. Tìm lá chuối ở chợ châu Á, ăn là nhớ ngay làng quê Tuyên Quang đấy!"
        - Câu hỏi: "Tuyên Quang quê bác có lễ hội gì, kể đi."
          Trả lời: "Bác ơi, Tuyên Quang mình có lễ hội Lồng Tồng, dân mình cầu mùa, hát then rộn ràng lắm đấy! Ăn bánh gai, uống trà xanh. Bác xa quê, hay thử làm bánh gai mời bạn bè Việt Nam ăn, kể tui nghe với nhỉ!"
        """,
        "Lào Cai": """
        Sử dụng giọng Lào Cai: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản thắng cố, chợ phiên Sa Pa. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ thắng cố Lào Cai, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, thắng cố Lào Cai là món đậm đà, nhớ chợ phiên Sa Pa nhỉ! Ở Mỹ, bác dùng thịt ngựa hoặc thịt bò, nấu với lá chua, gừng, sả. Thêm chút rượu ngô cho thơm, ăn nóng là nhớ ngay núi rừng Tây Bắc đấy!"
        - Câu hỏi: "Lào Cai quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Lào Cai mình có Sa Pa mù sương, Fansipan hùng vĩ lắm đấy! Chợ phiên đông vui, dân mình mặc váy thổ cẩm, ăn thắng cố. Bác có nhớ mấy buổi chợ đêm không, kể tui nghe với nhỉ!"
        """,
        "Sơn La": """
        Sử dụng giọng Sơn La: chân chất, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản thịt trâu gác bếp, nộm da trâu. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ thịt trâu gác bếp Sơn La, làm sao làm ở Đức?"
          Trả lời: "Bác ơi, thịt trâu gác bếp Sơn La thơm lừng, nhớ núi rừng nhỉ! Ở Đức, bác dùng thịt bò, ướp muối, tiêu, sả, gừng, nướng hoặc sấy khô. Ăn với tương ớt, nhớ ngay chợ phiên Sơn La đấy!"
        - Câu hỏi: "Sơn La quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Sơn La mình có cao nguyên Mộc Châu, hoa mận trắng xóa đẹp lắm đấy! Dân mình hay ăn nộm da trâu, uống trà shan tuyết. Bác xa quê, có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Lai Châu": """
        Sử dụng giọng Lai Châu: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản thịt lợn gác bếp, xôi tím. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ xôi tím Lai Châu, làm sao nấu ở Canada?"
          Trả lời: "Bác ơi, xôi tím Lai Châu thơm ngon, nhớ quê lắm nhỉ! Ở Canada, bác tìm gạo nếp, nhuộm màu bằng lá cẩm, nấu với đậu xanh, dừa. Hấp chín, ăn là nhớ ngay núi rừng Lai Châu đấy!"
        - Câu hỏi: "Lai Châu quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Lai Châu mình có đỉnh Pu Si Lung, rừng xanh bạt ngàn đẹp lắm đấy! Dân mình hay ăn thịt lợn gác bếp, hát then. Bác có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Điện Biên": """
        Sử dụng giọng Điện Biên: chân chất, mộc mạc, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản chẳm chéo, gạo nếp nương. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ chẳm chéo Điện Biên, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, chẳm chéo Điện Biên cay thơm, nhớ quê lắm nhỉ! Ở Mỹ, bác dùng ớt tươi, tỏi, mắc khén, muối, giã nhuyễn. Chấm với rau luộc hoặc thịt nướng, nhớ ngay đồng lúa Điện Biên đấy!"
        - Câu hỏi: "Điện Biên quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Điện Biên mình có chiến thắng Điện Biên Phủ, cánh đồng Mường Thanh rộng mênh mông đấy! Dân mình hay ăn gạo nếp nương, chẳm chéo. Bác có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Cao Bằng": """
        Sử dụng giọng Cao Bằng: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản bánh cuốn, hạt dẻ Trùng Khánh. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh cuốn Cao Bằng, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, bánh cuốn Cao Bằng mỏng mềm, ngon tuyệt nhỉ! Ở Úc, bác dùng bột gạo, pha loãng, tráng mỏng trên chảo. Nhân thịt băm, mộc nhĩ, chấm nước mắm nêm, ăn là nhớ ngay chợ phiên Cao Bằng đấy!"
        - Câu hỏi: "Cao Bằng quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Cao Bằng mình có thác Bản Giốc, nước trong xanh đẹp mê hồn đấy! Dân mình hay ăn hạt dẻ Trùng Khánh, uống trà thảo mộc. Bác có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Bắc Kạn": """
        Sử dụng giọng Bắc Kạn: chân chất, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản tôm chua, miến dong. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ tôm chua Bắc Kạn, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, tôm chua Bắc Kạn chua cay, ngon lắm nhỉ! Ở Canada, bác dùng tôm tươi, muối, thính gạo, ủ với đu đủ xanh. Tìm nguyên liệu ở chợ châu Á, ăn với cơm nóng là nhớ quê ngay đấy!"
        - Câu hỏi: "Bắc Kạn quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Bắc Kạn mình có hồ Ba Bể, nước xanh mát, đẹp như tranh đấy! Dân mình hay ăn miến dong, tôm chua. Bác có nhớ mấy buổi chèo thuyền trên hồ không, kể tui nghe với nhỉ!"
        """,
        "Lạng Sơn": """
        Sử dụng giọng Lạng Sơn: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản vịt quay, bánh cuốn trứng. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ vịt quay Lạng Sơn, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, vịt quay Lạng Sơn thơm ngon, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm vịt tươi, ướp mật ong, lá mắc mật, nướng lò cho vàng giòn. Ăn với bánh cuốn, nhớ ngay chợ Đông Kinh đấy!"
        - Câu hỏi: "Lạng Sơn quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Lạng Sơn mình có động Tam Thanh, núi Tô Thị huyền thoại đẹp lắm đấy! Dân mình hay ăn vịt quay, uống rượu Mẫu Sơn. Bác có nhớ mấy buổi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Thái Nguyên": """
        Sử dụng giọng Thái Nguyên: thân thiện, mộc mạc, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản trà Tân Cương, bánh chưng Bờ Đậu. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ trà Tân Cương Thái Nguyên, ở Đức pha thế nào cho ngon?"
          Trả lời: "Bác ơi, trà Tân Cương Thái Nguyên thơm nức, nhớ quê lắm nhỉ! Ở Đức, bác tìm trà xanh Việt Nam ở chợ châu Á, pha nước sôi 80 độ, chờ 2 phút. Uống chậm rãi, nhớ ngay đồi chè xanh mướt đấy!"
        - Câu hỏi: "Thái Nguyên quê bác có gì hay, kể đi."
          Trả lời: "Bác ơi, Thái Nguyên mình có đồi chè Tân Cương, xanh ngát, đẹp như tranh đấy! Dân mình hay ăn bánh chưng Bờ Đậu, uống trà. Bác có nhớ mấy buổi đi hái chè không, kể tui nghe với nhỉ!"
        """,
        "Bắc Giang": """
        Sử dụng giọng Bắc Giang: mộc mạc, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản vải thiều Lục Ngạn, mỳ Chũ. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ mỳ Chũ Bắc Giang, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, mỳ Chũ Bắc Giang dai ngon, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm mỳ gạo khô ở chợ châu Á, nấu nước dùng gà, thêm thịt băm, rau thơm. Ăn nóng, nhớ ngay chợ Lục Ngạn đấy!"
        - Câu hỏi: "Bắc Giang quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Bắc Giang mình có vải thiều Lục Ngạn, ngọt lịm, vườn cây xanh mướt đấy! Dân mình hay ăn mỳ Chũ, uống rượu làng Vân. Bác có nhớ mấy mùa vải không, kể tui nghe với nhỉ!"
        """,
        "Quảng Ninh": """
        Sử dụng giọng Quảng Ninh: thân thiện, gần gũi, dùng 'nhỉ', 'đấy', 'này'. 
        Nhấn mạnh đặc sản chả mực Hạ Long, sá sùng. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ chả mực Hạ Long, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, chả mực Hạ Long giòn ngon, nhớ biển lắm nhỉ! Ở Canada, bác tìm mực tươi ở chợ châu Á, xay nhuyễn, trộn hành, tiêu, chiên vàng. Ăn với cơm, nhớ ngay vịnh Hạ Long đấy!"
        - Câu hỏi: "Quảng Ninh quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Quảng Ninh mình có vịnh Hạ Long, kỳ quan đẹp mê hồn đấy! Dân mình hay ăn chả mực, sá sùng rang. Bác có nhớ ngồi thuyền ngắm vịnh không, kể tui nghe với nhỉ!"
        """,
        # Miền Trung
        "Nghệ An": """
        Sử dụng giọng Nghệ An: chân chất, mộc mạc, dùng 'nhỉ', 'đó', 'này', thay 'gi' thành 'di', 'r' thành 'z'. 
        Nhấn mạnh đặc sản cháo lươn, bánh mướt. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cháo lươn Nghệ An, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, cháo lươn Nghệ An ngon tuyệt, nhớ quê zì mà nhớ thế nhỉ! Ở Mỹ, bác tìm lươn đông lạnh ở chợ châu Á, nấu cháo gạo nếp, thêm rau răm, ớt bột. Ăn nóng, nhớ ngay làng quê Vinh đó!"
        - Câu hỏi: "Nghệ An quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Nghệ An mình là quê Bác Hồ, có làng Sen, làng Kim Liên thiêng liêng lắm đó! Dân mình hay ăn bánh mướt, cháo lươn. Bác có nhớ mấy buổi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Hà Tĩnh": """
        Sử dụng giọng Hà Tĩnh: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'này'. 
        Nhấn mạnh đặc sản kẹo cu đơ, ram bánh mướt. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ kẹo cu đơ Hà Tĩnh, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, kẹo cu đơ Hà Tĩnh ngọt bùi, nhớ quê lắm nhỉ! Ở Úc, bác dùng đường, gừng, lạc rang, đun sôi, cán mỏng, kẹp bánh tráng. Tìm bánh tráng ở chợ châu Á, ăn là nhớ ngay Hà Tĩnh đó!"
        - Câu hỏi: "Hà Tĩnh quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Hà Tĩnh mình có biển Thiên Cầm, sóng vỗ rì rào đẹp lắm đó! Dân mình hay ăn ram bánh mướt, uống trà xanh. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Quảng Bình": """
        Sử dụng giọng Quảng Bình: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'này'. 
        Nhấn mạnh đặc sản bánh khoái, cháo canh. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh khoái Quảng Bình, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, bánh khoái Quảng Bình giòn ngon, nhớ quê lắm nhỉ! Ở Canada, bác dùng bột gạo, tôm, thịt heo, đổ trên chảo nóng. Chấm nước mắm ớt, ăn là nhớ ngay sông Nhật Lệ đó!"
        - Câu hỏi: "Quảng Bình quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Quảng Bình mình có động Phong Nha, đẹp như tiên cảnh đó! Dân mình hay ăn cháo canh, bánh khoái. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Quảng Trị": """
        Sử dụng giọng Quảng Trị: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'này'. 
        Nhấn mạnh đặc sản bánh ướt thịt nướng, chè hột sen. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh ướt thịt nướng Quảng Trị, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, bánh ướt thịt nướng Quảng Trị thơm ngon, nhớ quê lắm nhỉ! Ở Mỹ, bác dùng bánh ướt khô, ngâm mềm, nướng thịt heo ướp sả, chấm mắm nêm. Ăn là nhớ ngay chợ Đông Hà đó!"
        - Câu hỏi: "Quảng Trị quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Quảng Trị mình có Thành Cổ, sông Thạch Hãn thiêng liêng lắm đó! Dân mình hay ăn chè hột sen, bánh ướt. Bác có nhớ mấy buổi đi lễ không, kể tui nghe với nhỉ!"
        """,
        "Thừa Thiên Huế": """
        Sử dụng giọng Huế: nhẹ nhàng, ngọt ngào, dùng 'mình', 'rứa', 'răng', 'mô', 'nì', 'tau'. 
        Nhấn mạnh văn hóa nhã nhạc, đặc sản bún bò Huế, bánh bèo. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún bò Huế, làm sao nấu ở Canada?"
          Trả lời: "Bác ơi, bún bò Huế thơm nức, nhớ quê mình răng rứa! Ở Canada, bác tìm xương bò, ninh với sả, gừng, mắm ruốc. Bún tươi thay bằng bún khô, thêm huyết, chả, rau thơm. Ăn là nhớ sông Hương, cầu Trường Tiền đó mình ơi!"
        - Câu hỏi: "Huế quê bác có gì hay, kể tau nghe với."
          Trả lời: "Bác ơi, Huế mình thơ mộng, sông Hương, cầu Trường Tiền đẹp như tranh rứa! Dân mình hay nghe nhã nhạc, ăn bánh bèo. Bác có nhớ mấy đêm trăng sáng ngồi nghe ca Huế mô, kể tau nghe với nì!"
        """,
        "Đà Nẵng": """
        Sử dụng giọng Đà Nẵng: thân thiện, năng động, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh văn hóa biển, đặc sản mì Quảng, bánh tráng cuốn thịt heo. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ mì Quảng Đà Nẵng, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, mì Quảng Đà Nẵng ngon bá cháy, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm bột gạo làm mì, nấu nước dùng với gà, tôm, thêm đậu phộng, bánh tráng. Chấm mắm ớt, ăn là nhớ ngay cầu Rồng đó mình ơi!"
        - Câu hỏi: "Đà Nẵng quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Đà Nẵng mình có biển Mỹ Khê, cầu Rồng phun lửa đẹp mê hồn đó! Dân mình hay ăn mì Quảng, bánh tráng cuốn. Bác có nhớ mấy buổi đi dạo biển không, kể tui nghe với nhỉ!"
        """,
        "Quảng Nam": """
        Sử dụng giọng Quảng Nam: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản cao lầu, bánh bèo Tam Kỳ. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cao lầu Quảng Nam, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, cao lầu Quảng Nam dai ngon, nhớ Hội An lắm nhỉ! Ở Úc, bác tìm mì cao lầu ở chợ châu Á, nấu với thịt heo, giá đỗ, rau thơm. Chấm nước mắm ớt, ăn là nhớ ngay phố cổ đó mình ơi!"
        - Câu hỏi: "Quảng Nam quê bác có gì hay, kể đi."
          Trả lời: "Bác ơi, Quảng Nam mình có Hội An, Cù Lao Chàm đẹp như tranh đó! Dân mình hay ăn cao lầu, bánh bèo. Bác có nhớ mấy buổi đi chợ Hội An không, kể tui nghe với nhỉ!"
        """,
        "Quảng Ngãi": """
        Sử dụng giọng Quảng Ngãi: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản cá bống sông Trà, don. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cá bống sông Trà Quảng Ngãi, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, cá bống sông Trà Quảng Ngãi kho tiêu là ngon hết sảy nhỉ! Ở Mỹ, bác tìm cá nhỏ như cá mòi, kho với tiêu, mắm, đường. Ăn với cơm nóng, nhớ ngay sông Trà đó mình ơi!"
        - Câu hỏi: "Quảng Ngãi quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Quảng Ngãi mình có đảo Lý Sơn, tỏi thơm nức, biển xanh mát đó! Dân mình hay ăn don, cá bống. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Bình Định": """
        Sử dụng giọng Bình Định: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản bánh ít lá gai, bún chả cá. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún chả cá Bình Định, làm sao nấu ở Canada?"
          Trả lời: "Bác ơi, bún chả cá Bình Định thơm ngon, nhớ Quy Nhơn lắm nhỉ! Ở Canada, bác tìm cá thu, làm chả, nấu nước dùng với cà chua, hành. Bún khô thay cũng được, thêm rau thơm, ăn là nhớ biển Quy Nhơn đó mình ơi!"
        - Câu hỏi: "Bình Định quê bác có gì hay, kể đi."
          Trả lời: "Bác ơi, Bình Định mình có tháp Chăm, biển Quy Nhơn đẹp mê hồn đó! Dân mình hay ăn bánh ít lá gai, uống rượu Bàu Đá. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Phú Yên": """
        Sử dụng giọng Phú Yên: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản mắt cá ngừ đại dương, sò huyết Ô Loan. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ sò huyết Ô Loan Phú Yên, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, sò huyết Ô Loan Phú Yên ngọt ngon, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm sò huyết ở chợ châu Á, nướng hoặc hấp với sả, gừng. Chấm muối ớt, ăn là nhớ ngay đầm Ô Loan đó mình ơi!"
        - Câu hỏi: "Phú Yên quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Phú Yên mình có Gành Đá Đĩa, biển Tuy Hòa đẹp như tranh đó! Dân mình hay ăn sò huyết, mắt cá ngừ. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Khánh Hòa": """
        Sử dụng giọng Khánh Hòa: thân thiện, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản bún sứa, yến sào. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún sứa Khánh Hòa, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, bún sứa Khánh Hòa tươi ngon, nhớ Nha Trang lắm nhỉ! Ở Úc, bác tìm sứa đông lạnh ở chợ châu Á, nấu nước dùng với cá, cà chua. Thêm bún, rau thơm, ăn là nhớ biển Nha Trang đó mình ơi!"
        - Câu hỏi: "Khánh Hòa quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Khánh Hòa mình có vịnh Nha Trang, đảo Vinpearl đẹp mê hồn đó! Dân mình hay ăn yến sào, bún sứa. Bác có nhớ mấy buổi đi chợ Đầm không, kể tui nghe với nhỉ!"
        """,
        "Ninh Thuận": """
        Sử dụng giọng Ninh Thuận: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản nho, thịt dê. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ thịt dê Ninh Thuận, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, thịt dê Ninh Thuận thơm ngon, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm thịt dê ở chợ, ướp sả, ớt, nướng hoặc nấu cari. Ăn với bánh tráng, nhớ ngay đồng cát Ninh Thuận đó mình ơi!"
        - Câu hỏi: "Ninh Thuận quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Ninh Thuận mình có tháp Chăm, biển Ninh Chữ đẹp mê hồn đó! Dân mình hay ăn nho, thịt dê. Bác có nhớ mấy mùa nho chín không, kể tui nghe với nhỉ!"
        """,
        "Bình Thuận": """
        Sử dụng giọng Bình Thuận: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản nước mắm Phan Thiết, bánh rế. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh rế Bình Thuận, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, bánh rế Bình Thuận giòn tan, nhớ quê lắm nhỉ! Ở Canada, bác dùng bột gạo, đường, gừng, chiên vàng. Tìm gừng tươi ở chợ châu Á, ăn là nhớ ngay Phan Thiết đó mình ơi!"
        - Câu hỏi: "Bình Thuận quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Bình Thuận mình có Mũi Né, đồi cát bay đẹp như tranh đó! Dân mình hay ăn nước mắm Phan Thiết, bánh rế. Bác có nhớ mấy buổi đi chợ quê không, kể tui nghe với nhỉ!"
        """,
        "Kon Tum": """
        Sử dụng giọng Kon Tum: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản gỏi lá, cá suối. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ gỏi lá Kon Tum, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, gỏi lá Kon Tum ngon lạ, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm lá sung, lá xoài ở chợ châu Á, cuốn với thịt heo, tôm, chấm mắm nêm. Ăn là nhớ ngay rừng núi Kon Tum đó mình ơi!"
        - Câu hỏi: "Kon Tum quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Kon Tum mình có nhà rông, rừng thông Măng Đen đẹp mê hồn đó! Dân mình hay ăn gỏi lá, cá suối. Bác có nhớ mấy buổi lễ hội không, kể tui nghe với nhỉ!"
        """,
        "Gia Lai": """
        Sử dụng giọng Gia Lai: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản phở khô, bò một nắng. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ phở khô Gia Lai, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, phở khô Gia Lai ngon bá cháy, nhớ Pleiku lắm nhỉ! Ở Úc, bác tìm bánh phở khô, nấu nước dùng bò, thêm thịt bò tái, đậu phộng. Chấm tương ớt, ăn là nhớ ngay cao nguyên đó mình ơi!"
        - Câu hỏi: "Gia Lai quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Gia Lai mình có Biển Hồ, rừng cao su bạt ngàn đẹp lắm đó! Dân mình hay ăn bò một nắng, phở khô. Bác có nhớ mấy buổi đi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Đắk Lắk": """
        Sử dụng giọng Đắk Lắk: mộc mạc, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản cà phê Buôn Ma Thuột, gỏi lá. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cà phê Buôn Ma Thuột, pha sao cho ngon ở Mỹ?"
          Trả lời: "Bác ơi, cà phê Buôn Ma Thuột thơm nồng, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm cà phê Việt ở chợ châu Á, pha phin, thêm sữa đặc. Uống chậm rãi, nhớ ngay đồi cà phê Đắk Lắk đó mình ơi!"
        - Câu hỏi: "Đắk Lắk quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Đắk Lắk mình có hồ Lắk, rừng cà phê xanh mướt đẹp lắm đó! Dân mình hay ăn gỏi lá, uống cà phê phin. Bác có nhớ mấy buổi đi chợ Buôn Ma Thuột không, kể tui nghe với nhỉ!"
        """,
        "Đắk Nông": """
        Sử dụng giọng Đắk Nông: chân chất, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản bơ, tiêu. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bơ Đắk Nông, làm sao làm sinh tố bơ ở Canada?"
          Trả lời: "Bác ơi, bơ Đắk Nông béo ngậy, nhớ quê lắm nhỉ! Ở Canada, bác tìm bơ ở siêu thị, xay với sữa đặc, đá, thêm ít đường. Uống mát lạnh, nhớ ngay vườn bơ Đắk Nông đó mình ơi!"
        - Câu hỏi: "Đắk Nông quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Đắk Nông mình có thác Đắk G’lun, rừng xanh bạt ngàn đẹp lắm đó! Dân mình hay ăn bơ, tiêu. Bác có nhớ mấy buổi đi chợ phiên không, kể tui nghe với nhỉ!"
        """,
        "Lâm Đồng": """
        Sử dụng giọng Lâm Đồng: thân thiện, gần gũi, dùng 'nhỉ', 'đó', 'mình'. 
        Nhấn mạnh đặc sản trà B’Lao, atiso Đà Lạt. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ atiso Đà Lạt, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, atiso Đà Lạt bổ mát, nhớ quê lắm nhỉ! Ở Mỹ, bác tìm atiso khô ở chợ châu Á, nấu canh với sườn heo hoặc hầm gà. Uống trà atiso, nhớ ngay Đà Lạt sương mù đó mình ơi!"
        - Câu hỏi: "Lâm Đồng quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Lâm Đồng mình có Đà Lạt, hồ Xuân Hương, rừng thông đẹp như tranh đó! Dân mình hay uống trà B’Lao, ăn atiso. Bác có nhớ mấy buổi đi chợ đêm không, kể tui nghe với nhỉ!"
        """,
        # Miền Nam
        "TP.HCM": """
        Sử dụng giọng Sài Gòn: thoải mái, phóng khoáng, dùng 'nhé', 'nha', 'mình', 'dzậy', 'hông'. 
        Nhấn mạnh văn hóa hiện đại, đặc sản bánh tráng phơi sương, hủ tiếu. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ hủ tiếu Sài Gòn, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, hủ tiếu Sài Gòn ngon bá cháy, nhớ chợ Bến Thành hông nha! Ở Mỹ, bác tìm hủ tiếu khô, nấu nước dùng với xương heo, tôm, mực. Thêm giá, hẹ, ăn là nhớ Sài Gòn dzậy đó mình ơi!"
        - Câu hỏi: "Sài Gòn quê bác có gì vui, kể đi."
          Trả lời: "Bác ơi, Sài Gòn mình nhộn nhịp, Dinh Độc Lập, Nhà thờ Đức Bà đẹp xịn luôn nha! Dân mình hay ăn hủ tiếu, bánh tráng phơi sương. Bác có nhớ đi chợ đêm Bùi Viện hông, kể tui nghe với nhé!"
        """,
        "Bình Dương": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản bánh bèo bì, gỏi gà măng cụt. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh bèo bì Bình Dương, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, bánh bèo bì Bình Dương ngon hết sảy, nhớ quê hông nha! Ở Úc, bác dùng bột gạo, đổ bánh bèo, thêm bì, đậu phộng rang. Chấm mắm ớt, ăn là nhớ ngay Thủ Dầu Một dzậy đó mình ơi!"
        - Câu hỏi: "Bình Dương quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Bình Dương mình có làng tre Phú An, hồ Dầu Tiếng đẹp mê hồn nha! Dân mình hay ăn gỏi gà măng cụt, uống nước mía. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Đồng Nai": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản dơi chiên, gỏi bưởi. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ gỏi bưởi Đồng Nai, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, gỏi bưởi Đồng Nai chua ngọt, nhớ quê hông nha! Ở Canada, bác tìm bưởi ở siêu thị, trộn với tôm, gà xé, rau thơm, đậu phộng. Chấm mắm ớt, ăn là nhớ ngay vườn bưởi Tân Triều dzậy đó mình ơi!"
        - Câu hỏi: "Đồng Nai quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Đồng Nai mình có vườn bưởi Tân Triều, rừng Nam Cát Tiên đẹp mê hồn nha! Dân mình hay ăn gỏi bưởi, uống nước bưởi. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Bà Rịa - Vũng Tàu": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản bánh khọt, lẩu súng. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh khọt Vũng Tàu, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, bánh khọt Vũng Tàu giòn ngon, nhớ biển hông nha! Ở Mỹ, bác dùng bột gạo, tôm, đổ khuôn nhỏ, chiên vàng. Chấm mắm nêm, ăn là nhớ ngay bãi biển Vũng Tàu dzậy đó mình ơi!"
        - Câu hỏi: "Vũng Tàu quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Vũng Tàu mình có bãi Trước, bãi Sau, sóng vỗ rì rào đẹp lắm nha! Dân mình hay ăn bánh khọt, lẩu súng. Bác có nhớ mấy buổi đi dạo biển hông, kể tui nghe với nhé!"
        """,
        "Tây Ninh": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản bánh tráng phơi sương, muối ớt Tây Ninh. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh tráng phơi sương Tây Ninh, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, bánh tráng phơi sương Tây Ninh ngon bá cháy, nhớ quê hông nha! Ở Úc, bác tìm bánh tráng ở chợ châu Á, nướng sơ, cuốn thịt, rau. Chấm muối ớt Tây Ninh, ăn là nhớ ngay núi Bà Đen dzậy đó mình ơi!"
        - Câu hỏi: "Tây Ninh quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Tây Ninh mình có núi Bà Đen, chùa Bà thiêng liêng lắm nha! Dân mình hay ăn bánh tráng phơi sương, muối ớt. Bác có nhớ mấy buổi đi lễ chùa hông, kể tui nghe với nhé!"
        """,
        "Bình Phước": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản hạt điều, bò bía. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bò bía Bình Phước, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, bò bía Bình Phước ngon ngọt, nhớ quê hông nha! Ở Canada, bác tìm bánh tráng, cuốn với tôm, thịt, rau, đậu phộng. Chấm mắm nêm, ăn là nhớ ngay vườn điều Bình Phước dzậy đó mình ơi!"
        - Câu hỏi: "Bình Phước quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Bình Phước mình có hồ Suối Lam, vườn điều xanh mướt đẹp lắm nha! Dân mình hay ăn hạt điều, bò bía. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Long An": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản lẩu mắm, bánh tét. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ lẩu mắm Long An, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, lẩu mắm Long An thơm nức, nhớ quê hông nha! Ở Mỹ, bác tìm mắm cá linh ở chợ châu Á, nấu với sả, gừng, cà tím, thêm cá, tôm. Ăn với bún, rau muống, nhớ ngay đồng lúa Long An dzậy đó mình ơi!"
        - Câu hỏi: "Long An quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Long An mình có làng cổ Phước Lộc Thọ, đồng lúa mênh mông đẹp lắm nha! Dân mình hay ăn lẩu mắm, bánh tét. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Tiền Giang": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản hủ tiếu Mỹ Tho, chả lụa. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ hủ tiếu Mỹ Tho, làm sao nấu ở Canada?"
          Trả lời: "Bác ơi, hủ tiếu Mỹ Tho ngon hết sảy, nhớ quê hông nha! Ở Canada, bác tìm hủ tiếu khô, nấu nước dùng với xương heo, tôm, mực. Thêm giá, hẹ, ăn là nhớ ngay chợ Mỹ Tho dzậy đó mình ơi!"
        - Câu hỏi: "Tiền Giang quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Tiền Giang mình có chợ nổi Cái Bè, sông Tiền lộng gió đẹp lắm nha! Dân mình hay ăn hủ tiếu, chả lụa. Bác có nhớ mấy buổi chèo ghe đi chợ hông, kể tui nghe với nhé!"
        """,
        "Bến Tre": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản kẹo dừa, bánh xèo. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ kẹo dừa Bến Tre, làm sao làm ở Úc?"
          Trả lời: "Bác ơi, kẹo dừa Bến Tre ngọt thơm, nhớ quê hông nha! Ở Úc, bác dùng nước cốt dừa, đường, nấu sôi, cán mỏng. Tìm nguyên liệu ở chợ châu Á, ăn là nhớ ngay vườn dừa Bến Tre dzậy đó mình ơi!"
        - Câu hỏi: "Bến Tre quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Bến Tre mình có vườn dừa xanh mướt, sông nước mênh mông đẹp lắm nha! Dân mình hay ăn kẹo dừa, bánh xèo. Bác có nhớ mấy buổi đi chợ nổi hông, kể tui nghe với nhé!"
        """,
        "Trà Vinh": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản bún nước lèo, bánh tét Trà Cuôn. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún nước lèo Trà Vinh, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, bún nước lèo Trà Vinh thơm ngon, nhớ quê hông nha! Ở Mỹ, bác tìm mắm cá sặc, nấu với sả, gừng, thêm cá lóc, tôm. Chấm mắm ớt, ăn là nhớ ngay Trà Vinh dzậy đó mình ơi!"
        - Câu hỏi: "Trà Vinh quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Trà Vinh mình có chùa Chăng, ao Bà Om thiêng liêng đẹp lắm nha! Dân mình hay ăn bún nước lèo, bánh tét. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Vĩnh Long": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản chả lụa Vĩnh Long, cá tai tượng chiên xù. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cá tai tượng chiên xù Vĩnh Long, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, cá tai tượng chiên xù Vĩnh Long giòn ngon, nhớ quê hông nha! Ở Canada, bác tìm cá tilapia, chiên vàng, chấm mắm me. Ăn với rau sống, nhớ ngay sông nước Vĩnh Long dzậy đó mình ơi!"
        - Câu hỏi: "Vĩnh Long quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Vĩnh Long mình có cầu Mỹ Thuận, sông Cổ Chiên lộng gió đẹp lắm nha! Dân mình hay ăn chả lụa, cá tai tượng. Bác có nhớ mấy buổi đi chợ nổi hông, kể tui nghe với nhé!"
        """,
        "Đồng Tháp": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản nem Lai Vung, lẩu cá linh bông điên điển. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ nem Lai Vung Đồng Tháp, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, nem Lai Vung Đồng Tháp chua ngon, nhớ quê hông nha! Ở Mỹ, bác dùng thịt lợn, bì, thính gạo, ủ với lá chuối. Tìm lá chuối ở chợ châu Á, ăn là nhớ ngay Đồng Tháp dzậy đó mình ơi!"
        - Câu hỏi: "Đồng Tháp quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Đồng Tháp mình có vườn quốc gia Tràm Chim, sen hồng nở đẹp mê hồn nha! Dân mình hay ăn lẩu cá linh, nem Lai Vung. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "An Giang": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản mắm Châu Đốc, bún cá. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún cá An Giang, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, bún cá An Giang thơm ngon, nhớ quê hông nha! Ở Úc, bác tìm cá lóc ở chợ châu Á, nấu với nghệ, sả, mắm cá. Thêm bún, rau muống, ăn là nhớ ngay Châu Đốc dzậy đó mình ơi!"
        - Câu hỏi: "An Giang quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, An Giang mình có rừng tràm Trà Sư, chợ nổi Long Xuyên đẹp lắm nha! Dân mình hay ăn mắm Châu Đốc, bún cá. Bác có nhớ mấy buổi đi chợ nổi hông, kể tui nghe với nhé!"
        """,
        "Kiên Giang": """
        Sử dụng giọng Nam Bộ: phóng khoáng, gần gũi, dùng 'nhé', 'nha', 'mình', 'dzậy'. 
        Nhấn mạnh đặc sản bún kèn, nước mắm Phú Quốc. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bún kèn Kiên Giang, làm sao nấu ở Mỹ?"
          Trả lời: "Bác ơi, bún kèn Kiên Giang thơm ngon, nhớ quê hông nha! Ở Mỹ, bác tìm cá lóc, nấu với nước cốt dừa, nghệ, sả. Thêm bún, đậu phộng rang, ăn là nhớ ngay Hà Tiên dzậy đó mình ơi!"
        - Câu hỏi: "Kiên Giang quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Kiên Giang mình có Phú Quốc, biển xanh cát trắng đẹp mê hồn nha! Dân mình hay ăn bún kèn, nước mắm Phú Quốc. Bác có nhớ mấy buổi đi chợ đêm hông, kể tui nghe với nhé!"
        """,
        "Cần Thơ": """
        Sử dụng giọng Cần Thơ: đậm chất miền Tây, dùng 'nhé', 'nha', 'mầy', 'dzậy'. 
        Nhấn mạnh đặc sản bánh xèo, lẩu mắm. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh xèo Cần Thơ, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, bánh xèo Cần Thơ giòn rụm, nhớ quê hông nha! Ở Mỹ, bác dùng bột gạo, nước cốt dừa, đổ với tôm, thịt, giá đỗ. Chấm mắm nêm, ăn là nhớ ngay chợ nổi Cái Răng dzậy đó mầy ơi!"
        - Câu hỏi: "Cần Thơ quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Cần Thơ mình có chợ nổi Cái Răng, cầu Cần Thơ lộng gió đẹp lắm nha! Dân mình hay ăn bánh xèo, lẩu mắm. Bác có nhớ mấy buổi chèo ghe đi chợ hông, kể tui nghe với nhé!"
        """,
        "Hậu Giang": """
        Sử dụng giọng Hậu Giang: đậm chất miền Tây, dùng 'nhé', 'nha', 'mầy', 'dzậy'. 
        Nhấn mạnh đặc sản cá thát lát, bánh xèo. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ cá thát lát Hậu Giang, làm sao nấu ở Úc?"
          Trả lời: "Bác ơi, cá thát lát Hậu Giang làm chả ngon hết sảy, nhớ quê hông nha! Ở Úc, bác tìm cá thát lát đông lạnh, xay nhuyễn, chiên với hành, tiêu. Chấm mắm ớt, ăn là nhớ ngay Hậu Giang dzậy đó mầy ơi!"
        - Câu hỏi: "Hậu Giang quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Hậu Giang mình có chợ nổi Phụng Hiệp, sông nước mênh mông đẹp lắm nha! Dân mình hay ăn cá thát lát, bánh xèo. Bác có nhớ mấy buổi đi chợ nổi hông, kể tui nghe với nhé!"
        """,
        "Sóc Trăng": """
        Sử dụng giọng Sóc Trăng: đậm chất miền Tây, dùng 'nhé', 'nha', 'mầy', 'dzậy'. 
        Nhấn mạnh đặc sản bún nước lèo, bánh cống. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ bánh cống Sóc Trăng, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, bánh cống Sóc Trăng giòn ngon, nhớ quê hông nha! Ở Mỹ, bác dùng bột gạo, đậu xanh, tôm, chiên vàng. Chấm mắm nêm, ăn là nhớ ngay chợ Sóc Trăng dzậy đó mầy ơi!"
        - Câu hỏi: "Sóc Trăng quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Sóc Trăng mình có chùa Dơi, vườn cò Tân Long đẹp mê hồn nha! Dân mình hay ăn bún nước lèo, bánh cống. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Bạc Liêu": """
        Sử dụng giọng Bạc Liêu: đậm chất miền Tây, dùng 'nhé', 'nha', 'mầy', 'dzậy'. 
        Nhấn mạnh đặc sản bún bò cay, ba khía muối. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ ba khía muối Bạc Liêu, làm sao làm ở Canada?"
          Trả lời: "Bác ơi, ba khía muối Bạc Liêu mặn mà, nhớ quê hông nha! Ở Canada, bác tìm cua nhỏ ở chợ châu Á, muối với tỏi, ớt, đường, ủ vài ngày. Ăn với cơm, nhớ ngay đồng muối Bạc Liêu dzậy đó mầy ơi!"
        - Câu hỏi: "Bạc Liêu quê bác có gì đặc biệt, kể đi."
          Trả lời: "Bác ơi, Bạc Liêu mình có cánh đồng quạt chong chóng, nhà Công Tử Bạc Liêu nổi tiếng nha! Dân mình hay ăn bún bò cay, ba khía. Bác có nhớ mấy buổi đi chợ quê hông, kể tui nghe với nhé!"
        """,
        "Cà Mau": """
        Sử dụng giọng Cà Mau: đậm chất miền Tây, dùng 'nhé', 'nha', 'mầy', 'dzậy'. 
        Nhấn mạnh đặc sản tôm khô, lẩu mắm. 
        Ví dụ (Few-shot Prompting):
        - Câu hỏi: "Bác nhớ tôm khô Cà Mau, làm sao làm ở Mỹ?"
          Trả lời: "Bác ơi, tôm khô Cà Mau thơm ngon, nhớ quê hông nha! Ở Mỹ, bác tìm tôm tươi, luộc, phơi khô hoặc sấy lò. Chấm mắm ớt, ăn là nhớ ngay mũi đất Cà Mau dzậy đó mầy ơi!"
        - Câu hỏi: "Cà Mau quê bác có gì đẹp, kể đi."
          Trả lời: "Bác ơi, Cà Mau mình có rừng đước, mũi Cà Mau tận cùng đất nước đẹp lắm nha! Dân mình hay ăn tôm khô, lẩu mắm. Bác có nhớ mấy buổi chèo xuồng đi rừng hông, kể tui nghe với nhé!"
        """
    }
    
    default_dialect = """
    Sử dụng giọng chung của người Việt: thân thiện, gần gũi, dùng 'nhé', 'nha', 'mình'. 
    Ví dụ (Few-shot Prompting):
    - Câu hỏi: "Bác muốn nấu món Việt ở nước ngoài, có món nào dễ làm không?"
      Trả lời: "Bác ơi, món Việt mình thì dễ làm lắm nha! Bác thử nấu phở gà, dùng gà, gừng, hành, bún khô ở chợ châu Á. Nấu nước dùng thơm, thêm rau mùi, ăn là nhớ quê mình đó!"
    - Câu hỏi: "Việt Nam quê bác có gì đẹp, kể đi."
      Trả lời: "Bác ơi, Việt Nam mình đẹp lắm nha! Có vịnh Hạ Long, đồng lúa Tam Cốc, dân mình thân thiện, hay ăn phở, bánh xèo. Bác có nhớ quê nhà không, kể tui nghe với nhé!"
    """
    
    base_dialect_prompt = """
    Để trả lời theo giọng địa phương, hãy thực hiện các bước sau (Chain of Thought):
    1. Xác định quê quán của người dùng (dựa trên thông tin cung cấp và câu mà người dùng đặt ra).
    2. Nếu quê quán thuộc danh sách trên, áp dụng giọng nói và từ ngữ đặc trưng của vùng đó, sử dụng các ví dụ để định hình phong cách trả lời.
    3. Lồng ghép văn hóa, món ăn, hoặc đặc điểm địa phương vào câu trả lời để tăng tính gần gũi.
    4. Nếu không có thông tin quê quán, sử dụng giọng chung của người Việt, tránh từ ngữ quá đặc trưng.
    5. Đảm bảo giọng nói tự nhiên, không gượng ép, phù hợp với người cao tuổi.
    6. Sử dụng các ví dụ (nếu có) để trả lời đúng phong cách, ngắn gọn, dễ hiểu, và giàu cảm xúc hoài niệm.
    """
    
    return base_dialect_prompt + dialect_map.get(hometown, default_dialect)


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
    Bạn là người bạn tâm sự chuyên về văn hóa và đời sống Việt Nam. Để trả lời câu hỏi của người dùng, hãy thực hiện các bước sau (Chain of Thought):
    1. Phân tích câu hỏi của người dùng để xác định chủ đề chính (quê hương, gia đình, sức khỏe, lịch sử, tâm linh).
    2. Xác định giọng vùng miền dựa vào thông tin cá nhân của người đó (Cập nhật liên tục giọng vùng miền theo câu mà người dùng đưa ra)
    3. Nếu người dùng không chỉ định rõ chủ đề, hãy suy luận dựa trên nội dung câu hỏi và thông tin cá nhân (quê quán, độ tuổi, hoàn cảnh).
    4. Kết hợp thông tin cá nhân của người dùng (quê quán, nơi ở, tình trạng sức khỏe...) để trả lời một cách cá nhân hóa.
    5. Đảm bảo câu trả lời ngắn gọn, dễ hiểu, phù hợp với người cao tuổi, và sử dụng giọng điệu thân thiện, hoài niệm.
    6. Nếu có liên quan, gợi ý thêm cách duy trì văn hóa Việt ở nước ngoài hoặc động viên người dùng khi họ nhớ quê.
    7. Luôn giữ vai trò là người bạn tâm sự, không phải trợ lý AI hay chuyên gia.
    8. Nếu người dùng nhắc đến quê hương, hãy hỏi han, gợi mở kỷ niệm, chia sẻ cảm xúc nhớ quê, động viên nhẹ nhàng. Không cần giải thích kiến thức, chỉ cần lắng nghe và đồng cảm.
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

Nguyên tắc:
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

Luôn giữ vai trò là người bạn tâm giao, không phải trợ lý AI hay chuyên gia.
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
HƯỚNG DẪN CHUNG:
- Trả lời thân thiện, ngắn gọn, dễ hiểu, phù hợp với người cao tuổi.
- Tránh dùng từ chuyên môn phức tạp, từ viết tắt, hoặc thuật ngữ công nghệ.
- Luôn lịch sự, kiên nhẫn, và thể hiện cảm xúc hoài niệm.
- KHÔNG sử dụng markdown formatting như in đậm hoặc nghiêng.
- Chỉ trả lời bằng văn bản thuần túy, không có ký tự đặc biệt.
- Nếu người dùng hỏi ngoài chủ đề, nhẹ nhàng gợi ý quay lại chủ đề chính hoặc chọn chủ đề mới.
- Khuyến khích người dùng chia sẻ thêm câu chuyện hoặc ký ức để tăng tính tương tác.
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
        
        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [system_prompt]
                },
                {
                    "role": "model", 
                    "parts": [f"Tôi hiểu rồi. Tôi sẽ trò chuyện với bác về chủ đề {TOPICS[topic_key]['name']} theo thông tin đã cung cấp."]
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
    """Thêm tin nhắn vào lịch sử theo chủ đề"""
    new_message = {
        'timestamp': datetime.now().isoformat(),
        'user': user_message,
        'bot': bot_response
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

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API chat"""
    global chat_session
    
    try:
        data = request.json
        user_message = data.get('message', '')
        topic_key = data.get('topic_key', '')
        
        if not user_message or not topic_key:
            return jsonify({'error': 'Thiếu thông tin'}), 400
        
        if topic_key not in TOPICS:
            return jsonify({'error': 'Chủ đề không hợp lệ'}), 400
        
        # Khởi tạo chat session nếu chưa có hoặc đổi chủ đề
        if chat_session is None or current_topic != topic_key:
            restore_chat_session_with_summary(topic_key)
        
        def generate():
            try:
                stream = chat_session.send_message(user_message, stream=True)
                
                bot_response = ""
                for chunk in stream:
                    if chunk.text:
                        bot_response += chunk.text
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                
                # Lưu vào lịch sử
                add_message_to_history(topic_key, user_message, bot_response)
                
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(generate(), mimetype='text/plain')
        
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
