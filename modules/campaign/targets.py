from database.db import create_user, add_user_to_campaign, get_users_by_campaign

def add_single_user_to_campaign(campaign_id, email):
    email = email.strip().lower()

    if not email:
        raise ValueError("Invalid email")

    user_id = create_user(email)
    add_user_to_campaign(campaign_id, user_id)

    return user_id


# def add_multiple_users_to_campaign(campaign_id, email_list):
#     added_users = []

#     for email in email_list:
#         try:
#             user_id = add_single_user_to_campaign(campaign_id, email)
#             added_users.append(user_id)
#         except Exception:
#             continue  # skip duplicates

#     return added_users


def list_targets(campaign_id):
    return get_users_by_campaign(campaign_id)
