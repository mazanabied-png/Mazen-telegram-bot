import telebot
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import json
import os

TOKEN = '8976847435:AAGkOm_yk7ydxk1PJ5gqAWlizEky_OR-LDA'
bot = telebot.TeleBot(TOKEN)

# سطر البروكسي الخاص بـ PythonAnywhere
apihelper.proxy = {'https': 'http://proxy.server:3128'}

bot.set_my_commands([
    BotCommand("start", "القائمة الرئيسية 🏠"),
    BotCommand("myid", "معرفة الـ ID الخاص بك 🆔")
])

MASTER_ADMIN = 1540807316 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data.json')

default_data = {
    "admins": [MASTER_ADMIN],
    "seasons": {f"Season {i}": {"First Term": {}, "Second Term": {}} for i in range(1, 5)},
    "competitions": {},
    "comp_stats": {},
    "stats": {}
}

if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if "seasons" not in data: data["seasons"] = default_data["seasons"]
        if "admins" not in data: data["admins"] = [MASTER_ADMIN]
        if "competitions" not in data: data["competitions"] = {}
        if "comp_stats" not in data: data["comp_stats"] = {}
        if "stats" not in data: data["stats"] = {}
    except:
        data = default_data
else:
    data = default_data

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

temp_comp_creation = {}
temp_student_sessions = {}

@bot.message_handler(commands=['myid'])
def get_id(message):
    bot.reply_to(message, f"الـ ID بتاعك هو:\n{message.chat.id}")

@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        markup = InlineKeyboardMarkup(row_width=2)
        for i in range(1, 5):
            markup.add(InlineKeyboardButton(f"Season {i}", callback_data=f"season_Season {i}"))
        
        if message.chat.id == MASTER_ADMIN or message.chat.id in data.get("admins", []):
            markup.add(InlineKeyboardButton("⚙️ لوحة الإدارة (إضافة أدمن)", callback_data="admin_panel"))
            
        bot.send_message(message.chat.id, "أهلاً بيك في كويزات ومسابقات الدفعة 🎓\nاختار السنة الدراسية:", reply_markup=markup)
    except Exception as e:
        if "message is not modified" not in str(e):
            bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    try:
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        req = call.data
        is_admin = (chat_id == MASTER_ADMIN or chat_id in data.get("admins", []))

        if req == "back_start":
            markup = InlineKeyboardMarkup(row_width=2)
            for i in range(1, 5):
                markup.add(InlineKeyboardButton(f"Season {i}", callback_data=f"season_Season {i}"))
            if is_admin:
                markup.add(InlineKeyboardButton("⚙️ لوحة الإدارة (إضافة أدمن)", callback_data="admin_panel"))
            bot.edit_message_text("أهلاً بيك في كويزات ومسابقات الدفعة 🎓\nاختار السنة الدراسية:", chat_id, msg_id, reply_markup=markup)

        elif req == "admin_panel":
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("➕ إضافة أدمن جديد", callback_data="add_admin"),
                InlineKeyboardButton("⬅️ رجوع للرئيسية", callback_data="back_start")
            )
            bot.edit_message_text("⚙️ لوحة الإدارة:", chat_id, msg_id, reply_markup=markup)

        elif req == "add_admin":
            bot.edit_message_text("ابعت الـ ID بتاع الأدمن الجديد:", chat_id, msg_id)
            bot.register_next_step_handler(call.message, save_new_admin)

        elif req.startswith("season_"):
            season = req.split("_")[1]
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("First Term", callback_data=f"term_{season}_First Term"),
                InlineKeyboardButton("Second Term", callback_data=f"term_{season}_Second Term"),
                InlineKeyboardButton("⬅️ رجوع", callback_data="back_start")
            )
            bot.edit_message_text(f"اختر الترم لـ {season}:", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("term_"):
            parts = req.split("_")
            season, term = parts[1], parts[2]
            term_key = f"{season}_{term}"
            
            markup = InlineKeyboardMarkup(row_width=1)
            subjects = data["seasons"][season][term]
            
            for sub in subjects.keys():
                markup.add(InlineKeyboardButton(sub, callback_data=f"sub_{season}_{term}_{sub}"))
                
            markup.add(InlineKeyboardButton("🏆 مسابقات هذا الترم", callback_data=f"complist_{term_key}"))

            if is_admin:
                markup.add(InlineKeyboardButton("⚙️➕ إضافة مادة هنا", callback_data=f"addsub_{season}_{term}"))
                
            markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data=f"season_{season}"))
            bot.edit_message_text(f"محتويات {season} - {term}\nاختار المادة أو قسم المسابقات:", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("addsub_"):
            parts = req.split("_")
            season, term = parts[1], parts[2]
            bot.edit_message_text(f"ابعتلي اسم المادة الجديدة لـ {season} - {term} ✍️:", chat_id, msg_id)
            bot.register_next_step_handler(call.message, save_new_subject, season, term)

        elif req.startswith("sub_"):
            parts = req.split("_")
            season, term, sub = parts[1], parts[2], parts[3]
            markup = InlineKeyboardMarkup(row_width=1)
            quizzes = data["seasons"][season][term][sub]
            for q in quizzes.keys():
                markup.add(InlineKeyboardButton(q, callback_data=f"quizmenu_{season}_{term}_{sub}_{q}"))
            if is_admin:
                markup.add(InlineKeyboardButton("➕ إضافة كويز Poll", callback_data=f"addquiz_{season}_{term}_{sub}"))
                markup.add(InlineKeyboardButton("🗑️ مسح هذه المادة", callback_data=f"ds_{season}_{term}_{sub}"))
            markup.add(InlineKeyboardButton("⬅️ رجوع", callback_data=f"term_{season}_{term}"))
            bot.edit_message_text(f"مادة: {sub}\nاختار الكويز:", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("complist_"):
            term_key = req.split("_")[1] + "_" + req.split("_")[2]
            season, term = term_key.split("_")[0], term_key.split("_")[1]
            
            markup = InlineKeyboardMarkup(row_width=1)
            comps = data["competitions"].get(term_key, {})
            
            if not comps:
                if is_admin:
                    markup.add(InlineKeyboardButton("➕ إضافة مسابقة جديدة هنا", callback_data=f"addcomp_{term_key}"))
                markup.add(InlineKeyboardButton("⬅️ رجوع للترم", callback_data=f"term_{season}_{term}"))
                bot.edit_message_text(f"🏆 مسابقات {season} - {term}:\nمفيش مسابقات مضافة هنا لسه.", chat_id, msg_id, reply_markup=markup)
                return

            for comp_name in comps.keys():
                if is_admin:
                    markup.add(
                        InlineKeyboardButton(f"🏆 {comp_name}", callback_data=f"compinfo_{term_key}_{comp_name}"),
                        InlineKeyboardButton(f"📊 نتائج {comp_name}", callback_data=f"compstats_{term_key}_{comp_name}"),
                        InlineKeyboardButton(f"🗑️ مسح {comp_name}", callback_data=f"delcomp_{term_key}_{comp_name}")
                    )
                else:
                    markup.add(InlineKeyboardButton(f"🏆 ابدأ مسابقة: {comp_name}", callback_data=f"startcomp_{term_key}_{comp_name}"))

            if is_admin:
                markup.add(InlineKeyboardButton("➕ إضافة مسابقة جديدة هنا", callback_data=f"addcomp_{term_key}"))
            markup.add(InlineKeyboardButton("⬅️ رجوع للترم", callback_data=f"term_{season}_{term}"))
            bot.edit_message_text(f"🏆 مسابقات {season} - {term}:\nاختار المسابقة:", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("addcomp_"):
            term_key = req.split("_")[1] + "_" + req.split("_")[2]
            bot.edit_message_text(f"ابعت اسم المسابقة الجديدة:", chat_id, msg_id)
            bot.register_next_step_handler(call.message, save_comp_name, term_key)

        elif req.startswith("compinfo_"):
            parts = req.split("_")
            term_key = parts[1] + "_" + parts[2]
            comp_name = parts[3]
            season, term = term_key.split("_")[0], term_key.split("_")[1]
            
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("📊 عرض نتائج الطلاب", callback_data=f"compstats_{term_key}_{comp_name}"),
                InlineKeyboardButton("🗑️ مسح المسابقة", callback_data=f"delcomp_{term_key}_{comp_name}"),
                InlineKeyboardButton("⬅️ رجوع للمسابقات", callback_data=f"complist_{term_key}")
            )
            bot.edit_message_text(f"🏆 إدارة مسابقة: {comp_name}\nعدد الأسئلة: {len(data['competitions'][term_key][comp_name])}", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("compstats_"):
            parts = req.split("_")
            comp_name = parts[3]
            stats = data["comp_stats"].get(comp_name, {})
            if not stats:
                bot.answer_callback_query(call.id, "مفيش حد حل المسابقة دي لسه!", show_alert=True)
            else:
                sorted_stats = sorted(stats.values(), key=lambda x: x['score'], reverse=True)
                msg_text = f"📊 لوحة شرف مسابقة ({comp_name}):\n\n"
                for idx, student in enumerate(sorted_stats, 1):
                    msg_text += f"{idx}. 👤 {student['name']} (ID: {student['student_id']}) ⟵ جاب: {student['score']} من {student['total']}\n"
                bot.send_message(chat_id, msg_text)

        elif req.startswith("delcomp_"):
            parts = req.split("_")
            term_key = parts[1] + "_" + parts[2]
            comp_name = parts[3]
            season, term = term_key.split("_")[0], term_key.split("_")[1]
            
            if term_key in data["competitions"] and comp_name in data["competitions"][term_key]:
                del data["competitions"][term_key][comp_name]
                if comp_name in data["comp_stats"]: del data["comp_stats"][comp_name]
                save_data()
            bot.answer_callback_query(call.id, "✅ تم مسح المسابقة بنجاح!", show_alert=True)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ رجوع للمسابقات", callback_data=f"complist_{term_key}"))
            bot.edit_message_text("✅ تم حذف المسابقة.", chat_id, msg_id, reply_markup=markup)

        elif req.startswith("startcomp_"):
            parts = req.split("_")
            term_key = parts[1] + "_" + parts[2]
            comp_name = parts[3]
            
            bot.edit_message_text(f"🏆 أهلاً بك في مسابقة ({comp_name})\n\nللبدء، من فضلك ابعتلي **اسمك الثلاثي والـ ID** في رسالة واحدة:", chat_id, msg_id, parse_mode="Markdown")
            temp_student_sessions[chat_id] = {'term_key': term_key, 'comp_name': comp_name, 'step': 'waiting_info'}

        elif req.startswith("ans_"):
            parts = req.split("_")
            term_key = parts[1] + "_" + parts[2]
            comp_name = parts[3]
            q_idx = int(parts[4])
            chosen_opt = int(parts[5])

            session = temp_student_sessions.get(chat_id)
            if not session or session.get('comp_name') != comp_name:
                bot.answer_callback_query(call.id, "انتهت الجلسة، ابدأ المسابقة من جديد.", show_alert=True)
                return

            questions = data["competitions"][term_key][comp_name]
            correct_opt = questions[q_idx]['correct']

            if chosen_opt == correct_opt:
                session['score'] += 1

            session['current_q'] += 1
            
            try:
                bot.delete_message(chat_id, msg_id)
            except:
                pass

            send_competition_question(chat_id, term_key, comp_name, session['current_q'])

        elif req == "add_more_q":
            bot.clear_step_handler_by_chat_id(chat_id)
            bot.send_message(chat_id, "ابعت السؤال التالي:")
            bot.register_next_step_handler(call.message, get_comp_question)

        elif req == "finish_comp":
            bot.clear_step_handler_by_chat_id(chat_id)
            if chat_id not in temp_comp_creation:
                bot.answer_callback_query(call.id, "انتهت الجلسة أو تم حفظها مسبقاً.", show_alert=True)
                return
            
            comp_info = temp_comp_creation[chat_id]
            term_key = comp_info['term_key']
            comp_name = comp_info['name']
            
            if term_key not in data["competitions"]:
                data["competitions"][term_key] = {}
                
            data["competitions"][term_key][comp_name] = comp_info['questions']
            save_data()
            del temp_comp_creation[chat_id]
            
            season, term = term_key.split("_")[0], term_key.split("_")[1]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ العودة لقائمة المسابقات", callback_data=f"complist_{term_key}"))
            bot.edit_message_text(f"🎉 مبروك! تم حفظ مسابقة ({comp_name}) في {season} - {term} بنجاح.", chat_id, msg_id, reply_markup=markup)

    except Exception as e:
        if "message is not modified" not in str(e):
            try:
                bot.send_message(call.message.chat.id, f"❌ حدث خطأ: {str(e)}")
            except:
                pass

def save_new_admin(message):
    try:
        if not message.text: return
        new_id = int(message.text.strip())
        if new_id not in data["admins"]:
            data["admins"].append(new_id)
            save_data()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ رجوع للرئيسية", callback_data="back_start"))
            bot.send_message(message.chat.id, f"✅ تم إضافة الأدمن بنجاح!", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "الأدمن ده متضاف قبل كده.")
    except ValueError:
        bot.send_message(message.chat.id, "❌ الـ ID لازم يكون أرقام بس.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

def save_new_subject(message, season, term):
    try:
        sub_name = message.text
        if not sub_name: return
        if sub_name not in data["seasons"][season][term]:
            data["seasons"][season][term][sub_name] = {}
            save_data()
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ رجوع للترم", callback_data=f"term_{season}_{term}"))
            bot.send_message(message.chat.id, f"✅ تم إضافة مادة: {sub_name}", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "المادة دي موجودة قبل كده.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء الحفظ: {str(e)}")

def save_comp_name(message, term_key):
    try:
        comp_name = message.text.strip()
        if not comp_name: return
        temp_comp_creation[message.chat.id] = {'term_key': term_key, 'name': comp_name, 'questions': []}
        bot.clear_step_handler_by_chat_id(message.chat.id)
        msg = bot.send_message(message.chat.id, f"✅ تم إنشاء مسابقة ({comp_name}).\n\nابعتلي **نص السؤال الأول** الآن:")
        bot.register_next_step_handler(msg, get_comp_question)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {str(e)}")

def get_comp_question(message):
    try:
        chat_id = message.chat.id
        if chat_id not in temp_comp_creation: return
        q_text = message.text.strip()
        if not q_text: return
        
        temp_comp_creation[chat_id]['current_q'] = q_text
        bot.send_message(chat_id, "ابعت دلوقتي **الاختيارات الأربعة**، كل اختيار في سطر لوحده:")
        bot.register_next_step_handler(message, get_comp_options)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")

def get_comp_options(message):
    try:
        chat_id = message.chat.id
        if chat_id not in temp_comp_creation: return
        options = message.text.strip().split('\n')
        
        if len(options) < 2:
            bot.send_message(chat_id, "❌ لازم تدخل اختيارين على الأقل. جرب ابعت الاختيارات تاني:")
            bot.register_next_step_handler(message, get_comp_options)
            return

        temp_comp_creation[chat_id]['current_options'] = options
        bot.send_message(chat_id, f"الاختيارات:\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)]) + "\n\nابعت **رقم الإجابة الصحيحة** فقط (مثال: 1 أو 2):")
        bot.register_next_step_handler(message, get_comp_correct)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")

def get_comp_correct(message):
    try:
        chat_id = message.chat.id
        if chat_id not in temp_comp_creation: return
        correct_idx = int(message.text.strip()) - 1
        
        comp_data = temp_comp_creation[chat_id]
        comp_data['questions'].append({
            'question': comp_data['current_q'],
            'options': comp_data['current_options'],
            'correct': correct_idx
        })

        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("➕ أضف سؤال آخر", callback_data="add_more_q"),
            InlineKeyboardButton("✅ إنهاء وحفظ المسابقة", callback_data="finish_comp")
        )
        bot.send_message(chat_id, f"✅ تم حفظ السؤال! إجمالي الأسئلة: {len(comp_data['questions'])}", reply_markup=markup)
    except ValueError:
        bot.send_message(chat_id, "❌ لازم تدخل رقم صحيح للإجابة الصح:")
        bot.register_next_step_handler(message, get_comp_correct)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ: {str(e)}")

@bot.message_handler(func=lambda msg: msg.chat.id in temp_student_sessions and temp_student_sessions[msg.chat.id].get('step') == 'waiting_info')
def get_student_info(message):
    chat_id = message.chat.id
    info_text = message.text.strip()
    if not info_text: return

    session = temp_student_sessions[chat_id]
    session['student_info'] = info_text
    session['score'] = 0
    session['current_q'] = 0
    session['step'] = 'playing'

    bot.send_message(chat_id, f"✅ تم تسجيل بياناتك بنجاح يا دكتور! هتبدأ المسابقة حالا بالتوفيق 🚀")
    send_competition_question(chat_id, session['term_key'], session['comp_name'], 0)

def send_competition_question(chat_id, term_key, comp_name, q_index):
    try:
        questions = data["competitions"][term_key][comp_name]
        
        if q_index >= len(questions):
            session = temp_student_sessions.get(chat_id, {})
            score = session.get('score', 0)
            total = len(questions)
            student_info = session.get('student_info', 'مجهول')

            if comp_name not in data["comp_stats"]: data["comp_stats"][comp_name] = {}
            data["comp_stats"][comp_name][str(chat_id)] = {
                'name': student_info,
                'student_id': str(chat_id),
                'score': score,
                'total': total
            }
            save_data()

            if chat_id in temp_student_sessions: del temp_student_sessions[chat_id]

            season, term = term_key.split("_")[0], term_key.split("_")[1]
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ العودة للترم", callback_data=f"term_{season}_{term}"))
            bot.send_message(chat_id, f"🏁 خلصت المسابقة يا دكتور!\n\n👤 الطالب: {student_info}\n🎯 نتيجتك النهائية: **{score} من {total}** 👍", reply_markup=markup, parse_mode="Markdown")
            return

        q_data = questions[q_index]
        markup = InlineKeyboardMarkup(row_width=1)
        for i, opt in enumerate(q_data['options']):
            markup.add(InlineKeyboardButton(opt, callback_data=f"ans_{term_key}_{comp_name}_{q_index}_{i}"))

        bot.send_message(chat_id, f"❓ السؤال ({q_index + 1} من {len(questions)}):\n\n{q_data['question']}", reply_markup=markup)
    except Exception as e:
        bot.send_message(chat_id, f"❌ حدث خطأ أثناء إرسال السؤال: {str(e)}")

print("🏆 البوت شغال الآن بالمسابقات داخل الترام...")
bot.remove_webhook()
bot.polling(none_stop=True, allowed_updates=['message', 'callback_query'])