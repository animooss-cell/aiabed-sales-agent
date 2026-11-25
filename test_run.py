from agent import DailySalesAgent

agent = DailySalesAgent()
results = agent.process_new_contacts(auto_open_whatsapp=False)
print("=" * 60)
print(f"تعداد {len(results)} پیام از فرم «تماس با ما» پردازش شد:")
print("=" * 60)
for idx, r in enumerate(results, 1):
    print(f"[{idx}] {r['name']} | شماره: {r['phone']}")
    print(f"    کانال درخواستی: {r['channel']} -> {r['action']}")
    print(f"    پیش‌نویس پیام:\n    {r['draft'][:100]}...\n")
