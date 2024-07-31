Dastur 2 qismadan iborat:
- sunc_server
- diod server

1. sync_server har bir virtual moshinada bo'ladi. Unda ishga tushiriladigan dasturlar:
- _watchdog.py
- client_app.py

2. diod_server papkasi diod serverda ishga tushiriladi

Dasturni ishga tushirish

```
pip install -r requirements.py
```


Qadam 1. diod_server/diod_server.py ni ishga tushiramiz
Qadam 2. _watchdog.py ni ishga tushiramiz. 
Qadam 3. client_app.py ni ishga tushiramiz.
Qadam 4. uploads papkasiga fayl ko'chiramiz 
Shunda _watchdog virtual moshinaning uploads papkasida paydo bo'lgan fayllarni umumiy bo'lgan mnt/data papkasiga qaytarilmas offset nomi bilan ko'chirib oladi va virutal moshinaning state.json fayliga shu virtual moshinaga tegishli bo'lgan fayllarni qo'shib qo'yadi (ya'ni har bir virtual papkada shu jarayon sodir bo'ladi)
Qadam 5. client_app mnt/data papkasidan o'ziga tegishli fayllarni olib, diod_serverga bo'laklab jo'natadai