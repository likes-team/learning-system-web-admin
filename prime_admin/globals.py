from app.auth.models import Role


SECRETARYREFERENCE = Role.objects(name="Secretary").get().id
PARTNERREFERENCE = Role.objects(name="Partner").get().id
MARKETERREFERENCE = Role.objects(name="Marketer").get().id