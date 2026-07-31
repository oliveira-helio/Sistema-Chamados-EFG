def serialize_user_for_audit(user):
    return {
        "matricula": user.matricula,
        "full_name": user.full_name,
        "email": user.email,
        "vinculo": user.vinculo,
        "area": user.area,
        "department": user.department,
        "cargo": user.cargo,
        "first_access": user.first_access,
        "is_active": user.is_active,
    }


def serialize_announcement_for_audit(announcement):
    return {
        "title": announcement.title,
        "is_published": announcement.is_published,
        "body": announcement.body,
    }
