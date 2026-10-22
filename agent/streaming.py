import json
import logging


async def safe_stream(source):
    """응답을 전달하고, 오류가 발생하면 화면에 알린다."""
    try:
        async for chunk in source:
            yield chunk
    except Exception:
        logging.getLogger(__name__).exception("채팅 스트림 처리 실패")
        error = {
            "type": "Error",
            "message": "요청 처리 중 오류가 발생했습니다. 서버 상태를 확인한 뒤 다시 시도해 주세요.",
        }
        yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"