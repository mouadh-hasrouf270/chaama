# نشر Backend Chaama على Render + Neon

## ما تحتويه الحزمة
- مشروع Django V10 كامل مع مسارات API والحجز والحسابات وملفات القضايا والفوترة وGoogle Calendar.
- إعدادات PostgreSQL، Gunicorn، WhiteNoise، CORS لواجهة `https://chaama-ten.vercel.app`.
- اختبار صحة `GET /health/` الذي يتحقق من اتصال قاعدة البيانات.
- `build.sh` و`render.yaml` و`.env.example`.

## 1) تجهيز GitHub
ضع **المجلد `django_backend`** في جذر مستودع `chaama` بجانب `frontend1`. لا ترفع `.env` أو `db.sqlite3`.
يمكنك إما إعداد Render يدويًا أو استعمال `render.yaml` من **جذر المستودع** لإنشاء Blueprint (انسخ render.yaml الموجود في هذه الحزمة إلى جذر المستودع).

## 2) Neon
أنشئ PostgreSQL من https://console.neon.tech/ ثم انسخ `DATABASE_URL` كاملاً مع `sslmode=require`.

## 3) Render — إعداد الخدمة يدويًا
https://dashboard.render.com/ → New → Web Service → Github repository `chaama`:
- Language: Python
- Branch: main
- Root Directory: `django_backend`
- Instance: Free
- Build Command: `bash build.sh`
- Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- Health Check Path: `/health/`

متغيرات البيئة في Render:
- `DATABASE_URL`: رابط Neon السري.
- `SECRET_KEY`: قيمة عشوائية طويلة (يمكن إنشاءها محليًا باستخدام Python secrets).
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS=chaama-backend.onrender.com` **غيّر الاسم إذا اختار Render اسمًا مختلفًا**.
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://chaama-ten.vercel.app`
- `BOOKING_TIME_ZONE=Africa/Algiers`
- `GOOGLE_CALENDAR_CLIENT_ID`, `GOOGLE_CALENDAR_CLIENT_SECRET`, `GOOGLE_CALENDAR_ENCRYPTION_KEY` من إعدادات مشروعك الأصلية.
- `GOOGLE_CALENDAR_REDIRECT_URI=https://chaama-ten.vercel.app/app/calendar`

**تنبيه:** إذا كانت كلمات مرور Google المخزنة مُشفرة بالمفتاح القديم فلا تستبدل مفتاح Fernet؛ وإذا بدأت قاعدة جديدة يمكنك إنشاء مفتاح جديد وربط Google من جديد.

## 4) إعداد Google Cloud
أضف بالضبط `https://chaama-ten.vercel.app/app/calendar` إلى Authorized redirect URIs ضمن OAuth Web Client. الموقع يعود إلى React ويُمرر code إلى API. أضف الدومين أيضًا ضمن Authorized JavaScript origins إن احتاجته إعداداتك.

## 5) Vercel
Settings → Environment Variables: `VITE_API_BASE_URL=https://chaama-backend.onrender.com/api` ثم Redeploy. انتبه: API الحجز موجود على `/api/v1/public/bookings/` وليس `/api/public/bookings/`.
تحققت من `frontend1/src/api/client.js` و`appointments.api.js`: الواجهة تضيف `/v1` تلقائيًا، لذلك يجب أن ينتهي المتغير بـ `/api` فقط.

## 6) التحقق
1. افتح `https://chaama-backend.onrender.com/health/` وتأكد من `{"status":"ok"}`.
2. اختبر تحميل الاختصاصات من `.../api/v1/public/practice-areas/`.
3. جرب حجزًا تجريبيًا من Vercel وتأكد من ظهوره في تقويم الإدارة وإنشاء ملف العميل.
4. اتصل بـGoogle Calendar واختبر إرسال الحدث. راقب Render Logs عند فشل المزامنة.

## قيود مهمة في الخطة المجانية
- Render ينام عند الخمول: قد يتأخر أول طلب.
- ملفات `private_evidence`, `private_uploads`, و`media` محلية ومؤقتة على Render. **لا ترفع وثائق عملاء فعلية**؛ يلزم تخزين سحابي خاص ثابت مع تنزيل محمي قبل الاختبار ببيانات حساسة.
- قاعدة Neon جديدة لا تتضمن حساب مديرك أو بيانات SQLite المحلية. أنشئ حساب إدارة بطريقة آمنة قبل الاختبار، ولا تضف كلمة مرور مدير إلى Git.
- إعداد build الحالي يشغّل migrations عند البناء. قد تحتاج إلى فحص سجلات Render لإصلاح أي خطأ ترحيلات.
- نجاح فحص الصياغة لا يغني عن اختبار Render الفعلي.
