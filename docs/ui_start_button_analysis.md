# تحلیل مشکل عدم نمایش DifficultyScreen

## توضیح مشکل
در منوی اصلی بازی دو دکمه START و CREDITS وجود دارد. زمانی که روی START کلیک می‌کنیم، انتظار داریم صفحه انتخاب سختی (DifficultyScreen) نمایش داده شود. اما در حال حاضر:
- نه بازی شروع می‌شود 
- نه صفحه DifficultyScreen روی صفحه ظاهر می‌شود

## تحلیل نقاط کلیدی کد

### 1. منطق Visibility دکمه START
```python
play_button = btn(
    "start",
    (240, 64),
    (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
    show_difficulty_screen,  
    lambda: not stats.game_active and not stats.credits_active and not difficulty_screen.active,
)
```
نکته مهم: شرط نمایش دکمه START شامل `not difficulty_screen.active` است. این یعنی:
- وقتی DifficultyScreen فعال می‌شود، دکمه START باید مخفی شود
- باید مطمئن شویم این تغییر وضعیت در همان فریم کلیک اتفاق می‌افتد

### 2. بررسی منطق Click در Button
از کد `src/entities/ui/elements/button/__init__.py`:
```python
if pygame.mouse.get_pressed()[0]:
    if not self.state.pressed:
        self.state.set_pressed(True)
else:
    if self.state.pressed:
        self.on_click()  # اینجا show_difficulty_screen صدا زده می‌شود
    self.state.set_pressed(False)
```

زنجیره رویدادها در کلیک:
1. دکمه موس رها می‌شود (نه زمان فشردن)
2. `on_click` که همان `show_difficulty_screen` است فراخوانی می‌شود
3. `difficulty_screen.active = True` می‌شود
4. دکمه START باید مخفی شود
5. `difficulty_screen.update()` باید در همان فریم اجرا شود

### 3. ترتیب Update ها در Game Loop
```python
# First update and draw difficulty screen (if active) 
if difficulty_screen.active:
    difficulty_screen.update()  # update includes draw logic
```

سوال کلیدی: آیا `active` شدن DifficultyScreen و اولین `update` آن در یک فریم اتفاق می‌افتند؟

## پیشنهادات برای Debug

### 1. لاگ در show_difficulty_screen
```python
def show_difficulty_screen():
    print("Show difficulty screen called")  # اضافه کردن این لاگ
    difficulty_screen.show()
```

### 2. لاگ در DifficultyScreen.update
```python
def update(self):
    if not self.active:
        return
    print("DifficultyScreen updating & drawing")  # اضافه کردن این لاگ
```

### 3. لاگ در Button.check_click
```python
def check_click(self):
    mouse_pos = pygame.mouse.get_pos()
    if self.top_rect.collidepoint(mouse_pos):
        print(f"Mouse over {self.text} button")  # اضافه کردن این لاگ
        if pygame.mouse.get_pressed()[0]:
            print(f"{self.text} button pressed")  # و این
```

## فرضیه‌های اصلی مشکل

1. **مشکل زمان‌بندی**: احتمالاً بین لحظه کلیک دکمه و اولین فریمی که DifficultyScreen باید رندر شود یک ناهماهنگی وجود دارد.

2. **مشکل Visibility**: ممکن است `difficulty_screen.active` درست تنظیم شود اما تغییر وضعیت نمایش دکمه‌ها در فریم درست اتفاق نیفتد.

3. **مشکل در Update/Draw**: احتمال دارد متدهای `update` و `draw` در DifficultyScreen به درستی فراخوانی شوند اما مشکلی در رندرینگ باشد.

## گام‌های پیشنهادی برای Debug

1. اضافه کردن لاگ‌های پیشنهادی برای تشخیص دقیق نقطه شکست در زنجیره رویدادها
2. بررسی ترتیب اجرای رویدادها در یک فریم
3. اطمینان از صحیح بودن مقادیر `active` و `visible` برای تمام المان‌های UI
4. بررسی این که آیا همه تغییرات وضعیت در یک فریم اتفاق می‌افتند یا خیر

با این لاگ‌ها می‌توان دقیقاً فهمید:
- آیا کلیک START تشخیص داده می‌شود
- آیا `show_difficulty_screen` فراخوانی می‌شود
- آیا DifficultyScreen فعال می‌شود
- آیا `update` و `draw` در فریم مناسب اجرا می‌شوند