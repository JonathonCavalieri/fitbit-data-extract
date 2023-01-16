import fitbit.authorization as auth


def main() -> None:
    user_token = auth.load_local_token()
    print(user_token)
    app_credentials = auth.load_local_credentials()
    print(app_credentials)
    token_new = auth.refresh_access_token(user_token, app_credentials)
    print(token_new)
    auth.save_local_token(token_new)


if __name__ == "__main__":
    main()
