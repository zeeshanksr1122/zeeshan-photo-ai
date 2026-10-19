
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
from rembg import remove, new_session

app = FastAPI(title="Zeeshan Photo AI")

session = None

@app.on_event("startup")
def load_model():
    global session
    session = new_session("u2net")

@app.get("/")
def home():
    return {
        "app": "Zeeshan Photo AI",
        "status": "running"
    }

@app.post("/edit/background")
async def edit_background(
    file: UploadFile = File(...),
    color: str = "white"
):
    if color not in ("white", "blue", "transparent"):
        raise HTTPException(400, "Choose white, blue, or transparent")

    if file.content_type not in (
        "image/jpeg", "image/png", "image/webp"
    ):
        raise HTTPException(400, "Upload JPG, PNG, or WEBP")

    data = await file.read()

    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image must be under 10 MB")

    try:
        original = Image.open(io.BytesIO(data)).convert("RGBA")
        cutout = remove(original, session=session)

        if color == "transparent":
            result = cutout
        else:
            bg = "white" if color == "white" else "#2389DA"
            background = Image.new("RGBA", cutout.size, bg)
            result = Image.alpha_composite(background, cutout)

        output = io.BytesIO()
        result.save(output, format="PNG")
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="image/png",
            headers={
                "Content-Disposition":
                'attachment; filename="zeeshan-photo.png"'
            }
        )
    except Exception:
        raise HTTPException(400, "Could not process this image")
