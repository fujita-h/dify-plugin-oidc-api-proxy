![Icon](./_assets/icon-oidc-api-proxy.jpg)

# OpenID Connect API Proxy 

[![GitHub Repo](https://img.shields.io/badge/GitHub_Repo-fujita--h/dify--plugin--oidc--api--proxy-blue?logo=github)](https://github.com/fujita-h/dify-plugin-oidc-api-proxy)  
![GitHub Release](https://img.shields.io/github/v/release/fujita-h/dify-plugin-oidc-api-proxy)
![GitHub License](https://img.shields.io/github/license/fujita-h/dify-plugin-oidc-api-proxy)

This plugin relays the API provided by Dify chat/workflow with OpenID Connect authentication enabled.

## Description

This plugin provides the same API endpoints as the Dify Chat/Workflow API, but uses OpenID Connect authentication instead of Dify's API key authentication.

You can use the endpoints created by this plugin to provide per-user authentication to the API.

## Features

### OpenID Connect authentication

This plugin uses OpenID Connect authentication to authenticate users. You can access the API with the access token obtained by authenticating with OpenID Connect.

### User parameter replacement

You can also replace the `user` parameter specified in the original API with OpenID Connect authenticated claim data. For example, if you replace it with an email address, the user's email address will be displayed on the Dify app log screen.

### Input claim data to the Chat/Workflow App

Plugin automatically inputs the claim data obtained by OpenID Connect authentication into the Chat/Workflow App. You can use the claim data in the Chat/Workflow App.

To use the claim data in the Chat/Workflow App, you need to specify the claim data name to the Start node's `input` parameter. For example, if you specify `__oidc_email` to the `input` parameter, you can use the email address in the Chat/Workflow App.

## Contributing

This plugin is open-source and contributions are welcome. Please visit the GitHub repository to contribute.
