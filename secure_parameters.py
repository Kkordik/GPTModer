# Secure Parameters Class (chat_id, etc.)
class SecureParameters:
    def __init__(self, called_function, message):
        self.message = message
        self.required_spm = function_required_spm.get(called_function, [])
        self.secure_params = {}

    def get_all(self):
        for method in self.required_spm:
            self.secure_params.update(method(self))
        return self.secure_params

    def get_chat_id(self):
        return {'chat_id': self.message.chat.id}


# Required secure parameters methods
function_required_spm = {
    'getChatMemberCount': [SecureParameters.get_chat_id],
    'setChatDescription': [SecureParameters.get_chat_id],
}
