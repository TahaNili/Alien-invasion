توضیح و راهنمای قدم‌به‌قدم برای رفع مشکلات شلیک AI

این سند به زبان فارسی شرح می‌دهد که چرا AI گلوله‌ها را از جهت یا نقطهٔ اشتباه شلیک می‌کند و چه کارهایی باید انجام بدهی تا مشکل حل شود. می‌توانی این محتوا را کپی کنی یا مستقیماً به‌عنوان مستند مرجع استفاده کنی.

## خلاصهٔ مشکل و علت‌های معمول

- مشکل اصلی: در حالت AI گلوله‌ها از جهت/نقطه‌ای شلیک می‌شوند که با شلیک بازیکن فرق دارد (ظاهر یا منطق بازی «تقلب» می‌کند).

- علت‌های معمول:
  1. AI زاویهٔ هدف را محاسبه می‌کند اما گلوله با استفاده از `ship.angle` یا با ساخت مستقیم `ShipBullet(ship)` ساخته می‌شود؛ در نتیجه گلوله از موقعیت/زاویهٔ داخل کشتی شلیک می‌شود نه از زاویهٔ AI.
  2. AI زاویه را پاس می‌دهد اما `fire_bullet` آن را اعمال نمی‌کند (مثلاً به خاطر debounce یا fallback) و override انجام نمی‌شود.
  3. مسیرهای متعدد برای ساخت گلوله وجود دارد که باعث ناسازگاری می‌شود؛ باید یک مسیر واحد (contract) برای ساخت گلوله وجود داشته باشد.
  4. (ثانویه) AI ممکن است `ship.angle` را موقتاً تغییر دهد تا جهت را «نمایشی» کند — این باعث می‌شود ظاهر بازیکن عوض شود.

هدف: AI باید مانند بازیکن رفتار کند — گلوله‌ها همیشه از «نوکِ کشتی» شلیک شوند و AI صرفاً زاویه را به تابع مرکزی ایجاد گلوله بدهد، بدون اینکه وضعیت `ship` را دستکاری کند.

## گام‌های عملی — کجا را نگاه کنی و چه چیزی را عوض کنی

1. فایل‌ها را بازبینی کن:
   - `src/game_functions.py` — باید تابع واحد `fire_bullet(ship, bullets, angle=None)` وجود داشته باشد که نقطهٔ مرکزی ایجاد گلوله است.
   - `src/bullet.py` — کلاس `ShipBullet` باید متد `set_angle_override(angle, source_ship)` داشته باشد که زاویه و موقعیت داخلی (rect.centerx/centery و x/y اعشاری) را تنظیم کند.
   - `src/ai_manager.py` — AI برای شلیک باید `gf.fire_bullet(ship, bullets, angle=fire_angle)` را صدا بزند و نه `ship.angle = fire_angle` یا ساخت دستی `ShipBullet` بدون override.
   - `src/ship.py` — ببین `ship.angle` چگونه محاسبه می‌شود (معمولاً با موس). AI نباید این مقدار را mutate کند.

2. مسیر شلیک یکتا برقرار کن:
   - فقط یک مکان برای ایجاد گلوله داشته باش (`fire_bullet`). اگر جاهای دیگری `ShipBullet(ship)` ساخته می‌شوند، آن‌ها را تغییر بده تا از `fire_bullet` استفاده کنند یا بلافاصله `set_angle_override` را صدا بزنند.

3. debounce (جلوگیری از شلیک دوگانه در همان فریم):
   - `fire_bullet` می‌تواند از `ship._last_fire_tick` یا مشابه برای جلوگیری از دو شلیک هم‌زمان استفاده کند. این خوب است اما هنگام تست توجه کن که debounce باعث نشود ظاهراً override انجام نشده باشد. برای تست بین دو فراخوانی `pygame.time.delay(1)` یا `pygame.time.wait(2)` قرار بده.

4. اطمینان از درست بودن `set_angle_override` در `src/bullet.py`:
   - باید `self.angle = float(angle)` را بگذارد.
   - باید نوکِ کشتی را محاسبه کند (مثلاً `x = ship.rect.centerx + sin(angle) * nose_offset` و `y = ship.rect.centery - cos(angle) * nose_offset`).
   - سپس `self.rect.centerx/centery = int(x), int(y)` و `self.x = float(self.rect.x)`, `self.y = float(self.rect.y)` را تنظیم کند.

5. بررسی AI:
   - در `src/ai_manager.py` مطمئن شو AI زاویه را پاس می‌دهد: `gf.fire_bullet(ship, bullets, angle=fire_angle)`.
   - اگر AI مستقیم `ship.angle` را set می‌کند یا تصویر کشتی را دستکاری می‌کند، آن را حذف کن و از پارامتر `angle` استفاده کن.

6. تست سادهٔ دستی (headless):
   - اسکریپتی بساز (مثلاً `tmp_ai_fire_test.py`) که:
     - `SDL_VIDEODRIVER=dummy` قرار می‌دهد، pygame را init می‌کند.
     - یک `FakeShip` یا `Ship` با موقعیت ثابت می‌سازد.
     - `bullets = Group()` می‌سازد.
     - `gf.fire_bullet(ship, bullets)` را صدا می‌زند و خروجی `rect.center` و `angle` را بررسی می‌کند.
     - سپس `pygame.time.delay(2)` و `gf.fire_bullet(ship, bullets, angle=some_angle)` را صدا می‌زند و مقایسه می‌کند آیا گلوله دوم در نوک کشتی با زاویهٔ مشخص ایجاد شده است یا نه.

## تغییرات مشخص پیشنهادی (کد) — ترتیب اجرای پیشنهادی

1. مرکزی کردن تولید گلوله:
   - `fire_bullet(ship, bullets, angle=None)` را به عنوان نقطهٔ واحد بساز که همیشه `ShipBullet(ship)` می‌سازد و در صورت ارائهٔ `angle`، `new_bullet.set_angle_override(angle, ship)` را فراخوانی کند.

2. پیاده‌سازی کامل `set_angle_override` در `src/bullet.py` (مثال):
   - `def set_angle_override(self, angle, source_ship):`
     - `self.angle = float(angle)`
     - `x = source_ship.rect.centerx + math.sin(self.angle) * nose_offset`
     - `y = source_ship.rect.centery - math.cos(self.angle) * nose_offset`
     - `self.rect.centerx = int(x)`
     - `self.rect.centery = int(y)`
     - `self.x = float(self.rect.x)`
     - `self.y = float(self.rect.y)`

3. حذف هر تغییر مستقیم `ship.angle` توسط AI و اطمینان از این که AI فقط `fire_bullet(..., angle=...)` می‌زند.

4. درج لاگ موقت داخل `fire_bullet` (اختیاری ولی کمک‌کننده):
   - اگر `angle is not None`: print یا logging بنویس `f"AI fire: angle={angle} spawn=({x},{y})"`.
   - اگر fallback رخ داد، log کن تا بفهمی چرا override عمل نکرد.

## نکات دیباگ و خطاهای متداول

- خطای `NoneType has no attribute get_rect`:
  - یعنی `TextureAtlas.get_sprite_texture(...)` تصویر را بارگذاری نکرده؛ در تست headless باید `TextureAtlas.get_sprite_texture` را mock یا fallback دهی (مثلاً برگرداندن یک `pygame.Surface((8,8))`).

- اگر `ai_bullet.angle` ست شده اما `rect` جای اشتباهی است:
  - احتمالاً `set_angle_override` زاویه را ست می‌کند اما `rect.center` یا `self.x/self.y` را آپدیت نمی‌کند.

- اگر گلوله از جای درست شلیک می‌شود اما حرکتش اشتباه است:
  - چک کن `update()` از `self.angle` برای محاسبهٔ dx/dy استفاده کند.

- اگر AI خیلی کم یا زیاد شلیک می‌کند:
  - مشکل ممکن است در `predict_fire()` یا در مدل ML باشد؛ برای دیباگ می‌توانی موقتاً مدل را bypass کرده و `should_fire=True` قرار دهی.

## معیارهای پذیرش (چطور مطمئن شوی مشکل حل شده)

- تست headless:
  - بعد از فراخوانی `gf.fire_bullet(ship, bullets, angle=ai_angle)`:
    - `ai_bullet.angle == ai_angle` (یا تقریباً برابر)
    - `ai_bullet.rect.centerx == int(ship.rect.centerx + sin(ai_angle)*nose_offset)`
    - `ai_bullet.rect.centery == int(ship.rect.centery - cos(ai_angle)*nose_offset)`

- در بازی واقعی:
  - وقتی AI شلیک می‌کند، بصری گلوله از نوک کشتی ظاهر شود (همانند شلیک بازیکن).
  - نرخ شلیک AI با نرخ شلیک بازیکن یکسان باشد (نه دو گلولهٔ ناخواسته در یک فریم).

## اگر خواستی من مستقیم اعمال کنم
می‌توانم این تغییرها را برایت اعمال کنم:
- `fire_bullet` را به‌عنوان نقطهٔ مرکزی تثبیت کنم.
- `set_angle_override` را کامل پیاده‌سازی کنم.
- اسکریپت‌های تست ساده و unit-testهای کوچک اضافه کنم.
- لاگ‌های موقت برای دیباگ اضافه کنم و سپس آن‌ها را پاک کنم.

اگر می‌خواهی من انجام دهم، فقط بنویس "ادامه بده و اعمال کن"؛ اگر می‌خواهی خودت انجام بدهی، بگو که فایل یا تابع خاصی را با مثال کد کوچک بخواهم بفرستم تا خودت ویرایش کنی.

---

این فایل را در پوشهٔ `reports` ایجاد کردم تا به‌راحتی بتوانی کپی یا به اشتراک بگذاری. اگر دوست داری نسخهٔ انگلیسی یا نسخهٔ خلاصه‌شده هم بسازم بگو تا اضافه کنم.
