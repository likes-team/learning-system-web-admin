# function to check file extension
def allowed_file(filename, file_type="image"):
    if file_type == "image":
        allowed = {'png', 'jpg', 'jpeg', 'gif'}
    elif file_type == "video":
        allowed = {'mp4', 'mov', 'mkv', 'avi'}
    else:
        raise Exception("Likes Error: file_type is not allowed")

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed
