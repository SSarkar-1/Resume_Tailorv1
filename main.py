from fastapi import FastAPI, UploadFile, File
from secrets import token_hex
import uvicorn

app=FastAPI(title="Backend")


@app.post("/upload")
async def upload(file:UploadFile=File(...)):
    file_ext=file.filename.split(".").pop() #Eg. png, jpeg etc
    file_name = token_hex(10)
    file_path = f"uploads/{file_name}.{file_ext}"
    with open(file_path, "wb") as f:
        content=await file.read()
        f.write(content)
        return {"success": True, "file path": file_path, "message": "File uploaded successfuly"}
    

    
if __name__=="__main__":
    uvicorn.run("main:app", host="127.0.0.1", reload=True)