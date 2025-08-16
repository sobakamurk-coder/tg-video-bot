import os, re, asyncio
from pathlib import Path
from aiogram import Bot, Dispatcher, F, types, html
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from aiogram.enums import ParseMode
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env var")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".webm")
URL_RE = re.compile(r"https?://\S+")

@dp.message(CommandStart())
async def start(m: types.Message):
    await m.answer(
        "Привет! Пришли прямую ссылку на видеофайл (.mp4/.mov/.webm), "
        "которое тебе можно скачивать — я пришлю файл.\n\n"
        "Пока работает только с прямыми ссылками."
    )

@dp.message(F.text.regexp(URL_RE))
async def handle_url(m: types.Message):
    url = URL_RE.search(m.text).group(0)
    pure = url.split("?")[0].lower()
    if not any(pure.endswith(ext) for ext in VIDEO_EXTS):
        await m.answer("Нужна прямая ссылка на видеофайл (.mp4/.mov/.webm).")
        return

    await m.answer("Скачиваю файл…")

    tmp = Path("downloads"); tmp.mkdir(exist_ok=True)
    file_path = tmp / ("video" + Path(pure).suffix or ".mp4")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            r = await client.get(url)
            r.raise_for_status()
            file_path.write_bytes(r.content)

        await m.answer_video(
            video=FSInputFile(file_path),
            caption=f"Готово: {html.quote(url)}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await m.answer(f"Ошибка скачивания: {e}")
    finally:
        try:
            if file_path.exists():
                file_path.unlink()
        except: pass

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
