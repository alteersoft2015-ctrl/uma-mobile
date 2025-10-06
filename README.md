# UMA Mobile App

تطبيق جوال لإدارة مستخدمي MikroTik عبر SSH.

## المتطلبات

- Python 3.6 أو أعلى
- Kivy
- Buildozer (لتحويل التطبيق إلى تطبيق جوال)

## التثبيت والتشغيل

### على جهاز الكمبيوتر

1. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

2. تشغيل التطبيق:
```bash
python main.py
```

### بناء تطبيق Android

1. تثبيت Buildozer:
```bash
pip install buildozer
```

2. تثبيت المتطلبات الإضافية:
```bash
# على Windows
pip install kivy_deps.sdl2 kivy_deps.glew kivy_deps.angle
```

3. بناء التطبيق:
```bash
buildozer android debug
```

4. تثبيت التطبيق على جهاز Android متصل:
```bash
buildozer android deploy
```

5. تشغيل التطبيق على جهاز Android متصل:
```bash
buildozer android run
```

## الوصف

هذا التطبيق يسمح لك بالاتصال بأجهزة MikroTik عبر SSH والبحث عن مستخدمي HotSpot و User Manager.

## الميزات

- الاتصال بأجهزة MikroTik عبر SSH
- البحث في مستخدمي HotSpot
- البحث في مستخدمي User Manager
- عرض النتائج بشكل منظم
- واجهة مستخدم عربية
- دعم كامل للغة العربية
