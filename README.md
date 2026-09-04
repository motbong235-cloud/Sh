# QR File Share

គេហទំព័រសាមញ្ញសម្រាប់ភាគីម្ខាង **upload ឯកសារ** ហើយបង្កើត **QR Code** ដើម្បីឲ្យភាគីម្ខាងទៀត **scan ហើយ download**។

## របៀបដំណើរការ
1. អ្នកប្រើម្នាក់បើកគេហទំព័រ → ជ្រើសរើសឯកសារ (ច្រើនក៏បាន) → ចុច "បង្កើត QR Code"
2. ប្រព័ន្ធរក្សាទុកឯកសារក្នុង folder ជាមួយ ID ខ្លីៗ ហើយបង្កើត QR ដែល encode link `/d/<id>`
3. អ្នកប្រើម្នាក់ទៀត scan QR (ដោយកាមេរ៉ាទូរស័ព្ទធម្មតា) → បើកទំព័រ download → ចុច download ម្តងមួយៗ ឬទាំងអស់ជា ZIP
4. Link ផុតកំណត់ស្វ័យប្រវត្តិបន្ទាប់ពី `EXPIRE_HOURS` (default 72 ម៉ោង)

## ដំណើរការក្នុងម៉ាស៊ីនផ្ទាល់ខ្លួន (local test)
```bash
pip install -r requirements.txt
python app.py
```
បើក http://localhost:5000

## Deploy លើ Render
1. Push code នេះទៅ GitHub repository
2. លើ Render.com → New → Web Service → ភ្ជាប់ repo
3. កំណត់៖
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. (ស្រេចចិត្ត) បន្ថែម Environment Variable:
   - `BASE_URL` = `https://your-app-name.onrender.com` (ដើម្បីឲ្យ QR generate link ត្រឹមត្រូវ)
   - `EXPIRE_HOURS` = `72` (ឬលេខផ្សេងតាមចង់បាន, `0` = មិនផុតកំណត់)
5. Deploy ហើយសាកល្បង upload/scan

## ចំណាំសំខាន់ៗ
- ឯកសាររក្សាទុកនៅលើ disk របស់ Render — គួរប្រើ **Render Persistent Disk** បើចង់ឲ្យឯកសារមិនបាត់ពេល redeploy
- Metadata (`BATCHES`) នៅក្នុង memory ប៉ុណ្ណោះ — បើប្រើ Render free tier ដែល restart ញឹកញាប់ គួរប្តូរទៅ SQLite ជំនួសដើម្បីកុំឲ្យ QR ចាស់ដាច់
- កំណត់ `MAX_CONTENT_LENGTH` ក្នុង `app.py` បើចង់ឲ្យ upload ធំជាង/តូចជាង 200MB
