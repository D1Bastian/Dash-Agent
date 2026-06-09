// auth.js - Utility for multi-provider OAuth handling

export function initProvider(provider) {
  const base = window.location.origin;
  const redirect = encodeURIComponent(`${base}/`);
  const params = {
    google: {
      client_id: process.env.GOOGLE_CLIENT_ID,
      redirect_uri: redirect,
      response_type: "token",
      scope: "openid email profile",
      state: "google"
    },
    github: {
      client_id: process.env.GITHUB_CLIENT_ID,
      redirect_uri: redirect,
      scope: "read:user repo",
      allow_signup: "true",
      state: "github"
    },
    microsoft: {
      client_id: process.env.MICROSOFT_CLIENT_ID,
      redirect_uri: redirect,
      response_type: "token",
      scope: "User.Read openid email profile",
      state: "microsoft"
    },
    anthropic: {
      client_id: process.env.ANTHROPIC_CLIENT_ID,
      redirect_uri: redirect,
      response_type: "token",
      scope: "openid email profile",
      state: "anthropic"
    },
    openai: {
      client_id: process.env.OPENAI_CLIENT_ID,
      redirect_uri: redirect,
      response_type: "token",
      scope: "openid email profile",
      state: "openai"
    }
  }[provider];

  if (!params) return null;
  const query = new URLSearchParams(params).toString();
  const urlMap = {
    google: "https://accounts.google.com/o/oauth2/v2/auth",
    github: "https://github.com/login/oauth/authorize",
    microsoft: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
    anthropic: "https://auth.anthropic.com/oauth/authorize",
    openai: "https://accounts.openai.com/o/oauth2/v2/auth"
  };
  return `${urlMap[provider]}?${query}`;
}

export function handleAuthCallback(provider, hash) {
  const params = new URLSearchParams(hash);
  const token = params.get("access_token") || params.get("code");
  const user_id = params.get("user_id") || "unknown";
  const name = params.get("name") || "User";
  const email = params.get("email") || "user@example.com";
  return { provider, token, user_id, name, email };
}
