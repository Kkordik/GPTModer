from pyrogram.enums import ChatMemberStatus

# Permissions and Secure Params Dict
permissions = {
    ChatMemberStatus.OWNER: {'getChatMemberCount', 'setChatDescription'},
    ChatMemberStatus.ADMINISTRATOR: {'getChatMemberCount', 'setChatDescription'},
    ChatMemberStatus.MEMBER: {'getChatMemberCount'}
}
