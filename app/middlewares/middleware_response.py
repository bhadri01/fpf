from fastapi.responses import JSONResponse

'''
=====================================================
# ✅ JSON Response with CORS
=====================================================
'''
def json_response_with_cors(content, status_code):
    return JSONResponse(
        content=content,
        status_code=status_code,
        headers={
            "Access-Control-Allow-Origin": "*",  # Modify this for security in production
            "Access-Control-Allow-Credentials": "true"
        }
    )
