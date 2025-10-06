# دليل المصادقة مع GitHub باستخدام Personal Access Token

## ما هو Personal Access Token (PAT)؟

Personal Access Token هو بديل لكلمة المرور عند المصادقة مع GitHub باستخدام واجهة برمجة التطبيقات (API) أو سطر الأوامر.

## كيفية إنشاء Personal Access Token

1. سجل الدخول إلى حسابك على GitHub
2. انقر على صورة ملفك الشخصي في الزاوية العلوية اليمنى واختر "Settings"
3. من القائمة الجانبية، انقر على "Developer settings"
4. انقر على "Personal access tokens" ثم "Tokens (classic)"
5. انقر على "Generate new token" ثم "Generate new token (classic)"
6. أعطِ الاسم رمزًا وصفًا (مثلاً "UMA Mobile App")
7. حدد تاريخ انتهاء الصلاحية
8. تحت "Select scopes"، حدد الصلاحيات المطلوبة:
   - `repo` - للوصول الكامل إلى المستودعات الخاصة والعامة
   - `workflow` - لتحديث سير عمل GitHub Actions
9. انقر على "Generate token"
10. **هام**: انسخ الرمز المميز واحفظه في مكان آمن. لن تتمكن من رؤيته مرة أخرى!

## كيفية استخدام Personal Access Token

### الطريقة 1: استخدام الرمز المميز ككلمة مرور

عندما يطلب منك Git اسم المستخدم وكلمة المرور:
1. أدخل اسم المستخدم الخاص بـ GitHub
2. أدخل Personal Access Token الذي أنشأته ككلمة المرور

### الطريقة 2: إضافة الرمز المميز إلى URL

يمكنك تعديل أمر git push ليشمل الرمز المميز:

```bash
git push https://YOUR_USERNAME:YOUR_TOKEN@github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

استبدل:
- `YOUR_USERNAME` باسم المستخدم الخاص بك على GitHub
- `YOUR_TOKEN` بالرمز المميز الذي أنشأته
- `YOUR_REPOSITORY` باسم المستودع الخاص بك

## الخطوات التالية بعد المصادقة الناجحة

بعد المصادقة بنجاح، يمكنك متابعة الخطوات في دليل BUILD_INSTRUCTIONS.md لبناء التطبيق.
