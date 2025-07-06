import urllib


def url_did_format(user_id,request):
    host = request.url.hostname
    port = request.url.port
    user_id = urllib.parse.unquote(user_id)
    if user_id.startswith("did:wba"):
        # 新增处理：如果 user_id 不包含 %3A，按 : 分割，第四个部分是数字，则把第三个 : 换成 %3A
        if "%3A" not in user_id:
            parts = user_id.split(":")
            if len(parts) > 4 and parts[3].isdigit():
                resp_did = ":".join(parts[:3]) + "%3A" + ":".join(parts[3:])
    elif len(user_id) == 16: # unique_id
        if port == 80 or port == 443:
            resp_did = f"did:wba:{host}:wba:user:{user_id}"
        else:
            resp_did = f"did:wba:{host}%3A{port}:wba:user:{user_id}"
    else :
        resp_did = "not_did_wba"

    return resp_did