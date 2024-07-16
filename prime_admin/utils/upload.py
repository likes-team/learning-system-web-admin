# function to check file extension
def allowed_file(filename):
    allowed = {'png', 'jpg', 'jpeg', 'gif'}

    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed
