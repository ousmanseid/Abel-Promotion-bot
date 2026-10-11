"""
Localization dictionary and formatting utilities for Abel Promotion bot.
Supports English (en) and Amharic (am).
"""

from typing import Dict, Any

MESSAGES: Dict[str, Dict[str, str]] = {
    # Language Selection
    "choose_language": {
        "en": "🌐 **Choose your preferred language / ቋንቋዎን ይምረጡ**",
        "am": "🌐 **ቋንቋዎን ይምረጡ / Choose your preferred language**",
    },
    "language_changed": {
        "en": "✅ Language changed to English.",
        "am": "✅ ቋንቋዎ ወደ አማርኛ ተቀይሯል።",
    },

    # Welcome & Start
    "welcome": {
        "en": (
            "👋 **Welcome to Abel Promotion!**\n\n"
            "Your trusted destination for social media marketing and promotion services. "
            "Explore our services, place an order, and track your order directly through Telegram.\n\n"
            "Please select an option from the menu below:"
        ),
        "am": (
            "👋 **እንኳን ወደ Abel Promotion በደህና መጡ!**\n\n"
            "የማህበራዊ ሚዲያ ማስተዋወቂያ እና የማርኬቲንግ አገልግሎቶቻችንን ይመልከቱ፣ "
            "ትዕዛዝ ያስገቡ፣ እና የትዕዛዝዎን ሁኔታ በቀጥታ በቴሌግራም ይከታተሉ።\n\n"
            "እባክዎ ከታች ካለው ዝርዝር ውስጥ ይምረጡ:"
        ),
    },

    # Main Menu Buttons (Reply Keyboard)
    "btn_services": {
        "en": "🛍️ Services",
        "am": "🛍️ አገልግሎቶች",
    },
    "btn_place_order": {
        "en": "📝 Place an Order",
        "am": "📝 ትዕዛዝ አስገባ",
    },
    "btn_my_orders": {
        "en": "📦 My Orders",
        "am": "📦 ትዕዛዞቼ",
    },
    "btn_payment_methods": {
        "en": "💳 Payment Methods",
        "am": "💳 የክፍያ መንገዶች",
    },
    "btn_my_profile": {
        "en": "👤 My Profile",
        "am": "👤 መለያዬ",
    },
    "btn_help": {
        "en": "❓ Help",
        "am": "❓ እርዳታ",
    },
    "btn_support": {
        "en": "📞 Contact Support",
        "am": "📞 ድጋፍ ያግኙ",
    },
    "btn_change_language": {
        "en": "🌐 Change Language",
        "am": "🌐 ቋንቋ ቀይር",
    },

    # Navigation buttons
    "btn_back": {
        "en": "⬅️ Back",
        "am": "⬅️ ተመለስ",
    },
    "btn_main_menu": {
        "en": "🏠 Main Menu",
        "am": "🏠 ዋና ሜኑ",
    },
    "btn_cancel": {
        "en": "❌ Cancel",
        "am": "❌ ሰርዝ",
    },

    # Platforms
    "select_platform": {
        "en": "📱 **Select a Social Media Platform:**",
        "am": "📱 **የማህበራዊ ሚዲያ መድረክ ይምረጡ:**",
    },
    "platform_instagram": {
        "en": "📸 Instagram",
        "am": "📸 ኢንስታግራም",
    },
    "platform_facebook": {
        "en": "📘 Facebook",
        "am": "📘 ፌስቡክ",
    },
    "platform_youtube": {
        "en": "▶️ YouTube",
        "am": "▶️ ዩቲዩብ",
    },

    # Services
    "select_service": {
        "en": "🔍 **Available {platform} Services:**\nSelect a service to see details and pricing:",
        "am": "🔍 **የ{platform} አገልግሎቶች:**\nዝርዝር መረጃና ዋጋ ለማየት አገልግሎት ይምረጡ:",
    },
    "no_services_found": {
        "en": "⚠️ No active services are currently available for this category.",
        "am": "⚠️ በአሁኑ ጊዜ በዚህ ዘርፍ የሚገኙ ንቁ አገልግሎቶች የሉም።",
    },
    "service_details": {
        "en": (
            "📌 **Service:** {name}\n"
            "📱 **Platform:** {platform}\n"
            "📝 **Description:** {description}\n"
            "💰 **Price:** {price} ETB {pricing_unit}\n"
            "⏱️ **Estimated Duration:** {duration}\n"
        ),
        "am": (
            "📌 **አገልግሎት:** {name}\n"
            "📱 **መድረክ:** {platform}\n"
            "📝 **መግለጫ:** {description}\n"
            "💰 **ዋጋ:** {price} ብር {pricing_unit}\n"
            "⏱️ **የሚፈጀው ጊዜ:** {duration}\n"
        ),
    },
    "btn_select_service": {
        "en": "✅ Select This Service",
        "am": "✅ ይህንን አገልግሎት ምረጥ",
    },

    # Ordering Flow
    "enter_target_link": {
        "en": (
            "🔗 **Please enter your public {platform} profile or post link:**\n\n"
            "*(Example: https://instagram.com/your_page or https://facebook.com/your_page)*\n"
            "⚠️ Note: Never share passwords, PINs, or private security codes."
        ),
        "am": (
            "🔗 **እባክዎ የህዝብ {platform} ሊንክዎን ያስገቡ:**\n\n"
            "*(ምሳሌ፦ https://instagram.com/your_page ወይም https://facebook.com/your_page)*\n"
            "⚠️ ማሳሰቢያ፦ የይለፍ ቃል (Password)፣ ፒን (PIN) ወይም ሚስጥራዊ ኮድ በጭራሽ አያጋሩ።"
        ),
    },
    "invalid_link": {
        "en": "⚠️ **Invalid Link!** Please enter a valid URL starting with http:// or https:// matching {platform}.",
        "am": "⚠️ **ልክ ያልሆነ ሊንክ!** እባክዎ በ http:// ወይም https:// የሚጀምር ትክክለኛ የ{platform} ሊንክ ያስገቡ።",
    },
    "enter_quantity": {
        "en": (
            "🔢 **Enter Quantity:**\n"
            "Minimum: {min_qty}\n"
            "Maximum: {max_qty}\n\n"
            "*(Unit price: {unit_price} ETB)*"
        ),
        "am": (
            "🔢 **የሚፈልጉትን መጠን ያስገቡ:**\n"
            "ዝቅተኛ: {min_qty}\n"
            "ከፍተኛ: {max_qty}\n\n"
            "*(የአንዱ ዋጋ: {unit_price} ብር)*"
        ),
    },
    "invalid_quantity": {
        "en": "⚠️ Please enter a valid number between {min_qty} and {max_qty}.",
        "am": "⚠️ እባክዎ በ{min_qty} እና {max_qty} መካከል ያለ ትክክለኛ ቁጥር ያስገቡ።",
    },
    "enter_customer_notes": {
        "en": (
            "📝 **Additional Instructions (Optional):**\n"
            "Enter any specific notes or target requirements, or click 'Skip' below:"
        ),
        "am": (
            "📝 **ተጨማሪ መመሪያዎች (አማራጭ):**\n"
            "ልዩ መስፈርቶች ካሉዎት ይጻፉ፣ ወይም ከታች 'ዝለል' የሚለውን ይጫኑ:"
        ),
    },
    "btn_skip": {
        "en": "⏩ Skip",
        "am": "⏩ ዝለል",
    },

    # Order Summary & Confirmation
    "order_summary": {
        "en": (
            "📋 **Order Summary**\n\n"
            "• **Service:** {service_name}\n"
            "• **Platform:** {platform}\n"
            "• **Quantity:** {quantity}\n"
            "• **Unit Price:** {unit_price} ETB\n"
            "• **Total Amount:** **{total_price} ETB**\n"
            "• **Target Link:** `{target_link}`\n"
            "• **Notes:** {notes}\n\n"
            "Please confirm your order to proceed to payment."
        ),
        "am": (
            "📋 **የትዕዛዝ ማጠቃለያ**\n\n"
            "• **አገልግሎት:** {service_name}\n"
            "• **መድረክ:** {platform}\n"
            "• **ብዛት:** {quantity}\n"
            "• **የአንዱ ዋጋ:** {unit_price} ብር\n"
            "• **ጠቅላላ ክፍያ:** **{total_price} ብር**\n"
            "• **የተላከው ሊንክ:** `{target_link}`\n"
            "• **ተጨማሪ ማስታወሻ:** {notes}\n\n"
            "ወደ ክፍያ ለመቀጠል እባክዎ ትዕዛዝዎን ያረጋግጡ።"
        ),
    },
    "btn_confirm_order": {
        "en": "✅ Confirm Order",
        "am": "✅ ትዕዛዙን አረጋግጥ",
    },
    "order_created": {
        "en": (
            "🎉 **Order #{order_code} Created Successfully!**\n\n"
            "Total Amount: **{total_price} ETB**\n"
            "Status: **Awaiting Payment**\n\n"
            "Please select your payment method below to view payment instructions:"
        ),
        "am": (
            "🎉 **የትዕዛዝ ቁጥር #{order_code} በተሳካ ሁኔታ ተፈጥሯል!**\n\n"
            "የሚከፈለው ክፍያ: **{total_price} ብር**\n"
            "ሁኔታ: **ክፍያ በመጠባበቅ ላይ**\n\n"
            "የክፍያ መመሪያዎችን ለማየት እባክዎ የክፍያ መንገድ ይምረጡ:"
        ),
    },
    "order_cancelled": {
        "en": "❌ Order creation was cancelled.",
        "am": "❌ የትዕዛዝ ሂደቱ ተሰርዟል።",
    },

    # Payment Methods & Instructions
    "select_payment_method": {
        "en": "💳 **Select Payment Method for Order #{order_code}:**",
        "am": "💳 **ለትዕዛዝ ቁጥር #{order_code} የክፍያ መንገድ ይምረጡ:**",
    },
    "payment_instruction_cbe": {
        "en": (
            "🏦 **Commercial Bank of Ethiopia (CBE) Payment Instructions**\n\n"
            "• **Order Code:** `{order_code}`\n"
            "• **Amount to Pay:** **{amount} ETB**\n"
            "• **Account Holder:** `{account_holder}`\n"
            "• **Account Number:** `{account_number}`\n\n"
            "📌 **Instructions:**\n"
            "1. Transfer the exact amount ({amount} ETB) via CBE Birr or CBE Mobile Banking.\n"
            "2. Take a screenshot of the completed transaction.\n"
            "3. Copy the transaction reference / FT number.\n"
            "4. Click **'Submit Payment Evidence'** below to upload your proof."
        ),
        "am": (
            "🏦 **የኢትዮጵያ ንግድ ባንክ (CBE) የክፍያ መመሪያ**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n"
            "• **የሚከፈለው መጠን:** **{amount} ብር**\n"
            "• **የሂሳብ ስም:** `{account_holder}`\n"
            "• **የሂሳብ ቁጥር:** `{account_number}`\n\n"
            "📌 **መመሪያ:**\n"
            "1. ትክክለኛውን መጠን ({amount} ብር) በ CBE Birr ወይም Mobile Banking ያስተላልፉ።\n"
            "2. የተጠናቀቀውን የዝውውር ደረሰኝ ስክሪንሾት ያንሱ።\n"
            "3. የትራንዛክሽን መለያ ቁጥር (FT ቁጥር) ይያዙ።\n"
            "4. ከታች **'የክፍያ ማስረጃ አስገባ'** የሚለውን በመጫን ይላኩ።"
        ),
    },
    "payment_instruction_telebirr": {
        "en": (
            "📱 **Telebirr Payment Instructions**\n\n"
            "• **Order Code:** `{order_code}`\n"
            "• **Amount to Pay:** **{amount} ETB**\n"
            "• **Account Holder:** `{account_holder}`\n"
            "• **Telebirr Number:** `{account_number}`\n\n"
            "📌 **Instructions:**\n"
            "1. Transfer the exact amount ({amount} ETB) using Telebirr SuperApp or `*127#`.\n"
            "2. Take a screenshot of the completed transaction SMS or app screen.\n"
            "3. Copy the transaction reference number.\n"
            "4. Click **'Submit Payment Evidence'** below to upload your proof."
        ),
        "am": (
            "📱 **የቴሌብር (Telebirr) የክፍያ መመሪያ**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n"
            "• **የሚከፈለው መጠን:** **{amount} ብር**\n"
            "• **የሂሳብ ስም:** `{account_holder}`\n"
            "• **የቴሌብር ቁጥር:** `{account_number}`\n\n"
            "📌 **መመሪያ:**\n"
            "1. ትክክለኛውን መጠን ({amount} ብር) በቴሌብር መተግበሪያ ወይም በ `*127#` ይላኩ።\n"
            "2. የደረሰኝ ስክሪንሾት ወይም የአጭር መልዕክት (SMS) ምስል ያንሱ።\n"
            "3. የትራንዛክሽን መለያ ቁጥር ይያዙ።\n"
            "4. ከታች **'የክፍያ ማስረጃ አስገባ'** የሚለውን በመጫን ይላኩ።"
        ),
    },
    "btn_submit_payment": {
        "en": "📤 Submit Payment Evidence",
        "am": "📤 የክፍያ ማስረጃ አስገባ",
    },

    # Payment Evidence Submission Flow
    "upload_screenshot_prompt": {
        "en": (
            "📸 **Please send the payment screenshot:**\n"
            "Upload the clear image or photo of your payment receipt.\n\n"
            "*(Send as a Photo)*"
        ),
        "am": (
            "📸 **እባክዎ የክፍያ ደረሰኙን ስክሪንሾት ይላኩ:**\n"
            "ግልጽ የሆነ የዝውውሩን ምስል ይላኩ።\n\n"
            "*(እንደ ፎቶ አድርገው ይላኩ)*"
        ),
    },
    "upload_reference_prompt": {
        "en": (
            "🔢 **Please enter the Transaction Reference Number:**\n"
            "*(e.g., FT26071... or Telebirr Transaction ID)*\n\n"
            "Or click 'Skip' if you don't have it."
        ),
        "am": (
            "🔢 **እባክዎ የትራንዛክሽን መለያ ቁጥር (Transaction Reference) ያስገቡ:**\n"
            "*(ምሳሌ፦ FT26071... ወይም የቴሌብር መለያ ቁጥር)*\n\n"
            "ከሌለዎት ከታች 'ዝለል' የሚለውን ይጫኑ።"
        ),
    },
    "payment_submitted_success": {
        "en": (
            "✅ **Payment Evidence Received!**\n\n"
            "• **Order Code:** `{order_code}`\n"
            "• **Amount:** {amount} ETB\n"
            "• **Method:** {method}\n"
            "• **Status:** **Payment Under Review**\n\n"
            "Our admin team will verify your transaction shortly. "
            "You will receive a notification as soon as it is approved."
        ),
        "am": (
            "✅ **የክፍያ ማስረጃው በተሳካ ሁኔታ ደርሷል!**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n"
            "• **የተከፈለው:** {amount} ብር\n"
            "• **መንገድ:** {method}\n"
            "• **ሁኔታ:** **ክፍያ በግምገማ ላይ**\n\n"
            "አስተዳዳሪዎቻችን ክፍያውን አረጋግጠው በቅርቡ ያሳውቁዎታል። "
            "ትዕዛዝዎ ሲጸድቅ ወዲያውኑ መልዕክት ይደርስዎታል።"
        ),
    },
    "duplicate_reference_error": {
        "en": "⚠️ This transaction reference has already been submitted for another order. Please contact support if you believe this is an error.",
        "am": "⚠️ ይህ የትራንዛክሽን መለያ ቁጥር ከዚህ በፊት ለሌላ ትዕዛዝ ጥቅም ላይ ውሏል። ስህተት ነው ብለው ካሰቡ ድጋፍ ያግኙ።",
    },

    # Customer Orders & History
    "no_orders_found": {
        "en": "📭 You haven't placed any orders yet. Click '📝 Place an Order' to get started!",
        "am": "📭 እስካሁን ምንም ትዕዛዝ አላስገቡም። ለመጀመር '📝 ትዕዛዝ አስገባ' የሚለውን ይጫኑ!",
    },
    "my_orders_title": {
        "en": "📦 **Your Orders History:**\nSelect an order to view full details and status:",
        "am": "📦 **የትዕዛዞችዎ ታሪክ:**\nዝርዝሩን እና ወቅታዊ ሁኔታውን ለማየት ትዕዛዝ ይምረጡ:",
    },
    "order_detail_view": {
        "en": (
            "🧾 **Order Details: #{order_code}**\n\n"
            "• **Service:** {service_name}\n"
            "• **Platform:** {platform}\n"
            "• **Quantity:** {quantity}\n"
            "• **Amount:** {total_price} ETB\n"
            "• **Target Link:** `{target_link}`\n"
            "• **Status:** **{status_text}**\n"
            "• **Date:** {date}\n"
            "{payment_info}"
        ),
        "am": (
            "🧾 **የትዕዛዝ ዝርዝር: #{order_code}**\n\n"
            "• **አገልግሎት:** {service_name}\n"
            "• **መድረክ:** {platform}\n"
            "• **ብዛት:** {quantity}\n"
            "• **ክፍያ:** {total_price} ብር\n"
            "• **የተላከው ሊንክ:** `{target_link}`\n"
            "• **ሁኔታ:** **{status_text}**\n"
            "• **ቀን:** {date}\n"
            "{payment_info}"
        ),
    },

    # Status Labels
    "status_awaiting_payment": {
        "en": "⏳ Awaiting Payment",
        "am": "⏳ ክፍያ በመጠባበቅ ላይ",
    },
    "status_payment_under_review": {
        "en": "🔍 Payment Under Review",
        "am": "🔍 ክፍያ በግምገማ ላይ",
    },
    "status_payment_rejected": {
        "en": "❌ Payment Rejected",
        "am": "❌ ክፍያ ውድቅ ተደርጓል",
    },
    "status_paid": {
        "en": "💳 Paid (Verified)",
        "am": "💳 ተከፍሏል (ተረጋግጧል)",
    },
    "status_approved": {
        "en": "✅ Approved",
        "am": "✅ ጸድቋል",
    },
    "status_in_progress": {
        "en": "⚙️ In Progress",
        "am": "⚙️ በሂደት ላይ",
    },
    "status_completed": {
        "en": "🎉 Completed",
        "am": "🎉 ተጠናቋል",
    },
    "status_cancelled": {
        "en": "🚫 Cancelled",
        "am": "🚫 ተሰርዟል",
    },
    "status_refund_review": {
        "en": "🔄 Refund Review",
        "am": "🔄 የተመላሽ ግምገማ",
    },
    "status_refunded": {
        "en": "↩️ Refunded",
        "am": "↩️ ተመላሽ ተደርጓል",
    },

    # Customer Profile
    "profile_text": {
        "en": (
            "👤 **Customer Profile**\n\n"
            "• **Telegram ID:** `{telegram_id}`\n"
            "• **Name:** {name}\n"
            "• **Username:** {username}\n"
            "• **Language:** {language}\n"
            "• **Total Orders:** {total_orders}\n"
            "• **Completed Orders:** {completed_orders}\n"
            "• **Joined:** {joined_date}\n"
        ),
        "am": (
            "👤 **የደንበኛ መለያ**\n\n"
            "• **የቴሌግራም መለያ (ID):** `{telegram_id}`\n"
            "• **ስም:** {name}\n"
            "• **የተጠቃሚ ስም:** {username}\n"
            "• **ቋንቋ:** {language}\n"
            "• **ጠቅላላ ትዕዛዞች:** {total_orders}\n"
            "• **የተጠናቀቁ ትዕዛዞች:** {completed_orders}\n"
            "• **የተመዘገቡበት ቀን:** {joined_date}\n"
        ),
    },

    # Help & Contact Support
    "help_text": {
        "en": (
            "ℹ️ **How to Use Abel Promotion Bot:**\n\n"
            "1. **Browse Services:** Tap '🛍️ Services' to explore legitimate marketing options.\n"
            "2. **Place an Order:** Tap '📝 Place an Order', provide your profile/post link and quantity.\n"
            "3. **Make Payment:** Transfer via CBE or Telebirr and submit the screenshot.\n"
            "4. **Track Order:** Tap '📦 My Orders' anytime to see real-time status updates.\n\n"
            "🔒 **Security & Policy Notice:**\n"
            "We never ask for passwords, bank PINs, or SMS codes. All marketing uses authentic, policy-compliant promotional strategies."
        ),
        "am": (
            "ℹ️ **Abel Promotion ቦትን እንዴት መጠቀም ይቻላል?**\n\n"
            "1. **አገልግሎቶችን ይመልከቱ:** '🛍️ አገልግሎቶች' በመጫን ያሉትን አማራጮች ይመልከቱ።\n"
            "2. **ትዕዛዝ ያስገቡ:** '📝 ትዕዛዝ አስገባ'ን ይጫኑ፣ የገጽዎን ሊንክ እና የሚፈልጉትን መጠን ያስገቡ።\n"
            "3. **ክፍያ ይፈጽሙ:** በንግድ ባንክ (CBE) ወይም በቴሌብር ከፍለው የደረሰኝ ስክሪንሾት ያስገቡ።\n"
            "4. **ትዕዛዝዎን ይከታተሉ:** በማንኛውም ጊዜ '📦 ትዕዛዞቼ'ን በመጫን የትዕዛዝዎን ደረጃ ይከታተሉ።\n\n"
            "🔒 **የደህንነት ማሳሰቢያ:**\n"
            "የይለፍ ቃል፣ የባንክ ፒን ወይም የኤስኤምኤስ ኮድ በጭራሽ አንጠይቅም። ሁሉም አገልግሎቶች ህጋዊና ደህንነታቸው የተጠበቁ ናቸው።"
        ),
    },
    "support_intro": {
        "en": (
            "📞 **Abel Promotion Customer Support**\n\n"
            "Please send your question, order issue, or message below. "
            "Our support team will review your ticket and reply directly to your chat."
        ),
        "am": (
            "📞 **የ Abel Promotion የደንበኞች ድጋፍ አገልግሎት**\n\n"
            "እባክዎ ጥያቄዎን፣ የትዕዛዝዎን ጉዳይ ወይም አስተያየትዎን ከታች ይጻፉ። "
            "የድጋፍ ቡድናችን መልዕክትዎን አይቶ በቀጥታ በቴሌግራም ምላሽ ይሰጥዎታል።"
        ),
    },
    "ticket_created": {
        "en": "✅ **Support Ticket #{ticket_code} Created!**\nOur team has been notified and will reply shortly.",
        "am": "✅ **የድጋፍ ጥያቄ ቁጥር #{ticket_code} ተመዝግቧል!**\nመልዕክትዎ ደርሶናል፤ በቅርቡ ምላሽ እንሰጥዎታለን።",
    },

    # Order Approval & Rejection Notifications
    "order_approved_notify": {
        "en": (
            "✅ **Your order has been APPROVED!**\n\n"
            "• **Order ID:** `{order_code}`\n"
            "• **Service:** {service_name}\n"
            "• **Amount:** {total_price} ETB\n\n"
            "Your order has been accepted and will be processed. We will notify you when work starts and when it is completed."
        ),
        "am": (
            "✅ **ትዕዛዝዎ ጸድቋል!**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n"
            "• **አገልግሎት:** {service_name}\n"
            "• **የተከፈለው:** {total_price} ብር\n\n"
            "ትዕዛዝዎ ተቀባይነት አግኝቷል፤ ስራው ሲጀመር እና ሲጠናቀቅ ወዲያውኑ መልዕክት ይደርስዎታል።"
        ),
    },
    "order_rejected_notify": {
        "en": (
            "❌ **Your order was not approved.**\n\n"
            "• **Order ID:** `{order_code}`\n"
            "• **Reason:** {reason}\n\n"
            "{refund_note}"
            "Please contact support if you need clarification."
        ),
        "am": (
            "❌ **ትዕዛዝዎ አልጸደቀም።**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n"
            "• **ምክንያት:** {reason}\n\n"
            "{refund_note}"
            "ተጨማሪ ማብራሪያ ከፈለጉ እባክዎ ድጋፍ ያግኙ።"
        ),
    },
    "order_support_message_received": {
        "en": (
            "📩 **Message from Abel Promotion Support**\n\n"
            "• **Order ID:** `{order_code}`\n\n"
            "{message_text}\n\n"
            "*(You can tap '✍️ Reply to Support' below to reply)*"
        ),
        "am": (
            "📩 **ከ Abel Promotion ድጋፍ የተላከ መልዕክት**\n\n"
            "• **የትዕዛዝ ቁጥር:** `{order_code}`\n\n"
            "{message_text}\n\n"
            "*(ምላሽ ለመስጠት ከታች '✍️ ለድጋፍ ምላሽ ይስጡ' የሚለውን ይጫኑ)*"
        ),
    },
    "btn_reply_to_support": {
        "en": "✍️ Reply to Support",
        "am": "✍️ ለድጋፍ ምላሽ ይስጡ",
    },

    "status_rejected": {
        "en": "❌ Rejected",
        "am": "❌ ውድቅ ተደርጓል",
    },

    # Generic & Error Messages
    "general_error": {
        "en": "⚠️ Something went wrong. Please try again later or contact support.",
        "am": "⚠️ ችግር አጋጥሟል። እባክዎ ትንሽ ቆይተው እንደገና ይሞክሩ ወይም ድጋፍ ያግኙ።",
    },
    "unauthorized_admin": {
        "en": "⛔ You are not authorized to perform administrative actions.",
        "am": "⛔ ይህንን የአስተዳዳሪ ተግባር ለመፈጸም ፈቃድ የለዎትም።",
    },
}

def t(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Retrieve localized message formatted with kwargs."""
    lang_code = "am" if lang == "am" else "en"
    msg_dict = MESSAGES.get(key)
    if not msg_dict:
        return key
    text = msg_dict.get(lang_code, msg_dict.get("en", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text

def get_status_display(status: str, lang: str = "en") -> str:
    """Translate raw status code to user-friendly label."""
    mapping = {
        "pending_payment": "status_awaiting_payment",
        "Awaiting Payment": "status_awaiting_payment",
        "payment_under_review": "status_payment_under_review",
        "Payment Under Review": "status_payment_under_review",
        "paid": "status_paid",
        "Paid": "status_paid",
        "approved": "status_approved",
        "Approved": "status_approved",
        "rejected": "status_rejected",
        "Payment Rejected": "status_rejected",
        "in_progress": "status_in_progress",
        "In Progress": "status_in_progress",
        "completed": "status_completed",
        "Completed": "status_completed",
        "cancelled": "status_cancelled",
        "Cancelled": "status_cancelled",
        "refund_pending": "status_refund_review",
        "Refund Review": "status_refund_review",
        "refunded": "status_refunded",
        "Refunded": "status_refunded",
    }
    key = mapping.get(status, "")
    if key:
        return t(key, lang=lang)
    return status
