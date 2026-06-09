from dataclasses import dataclass


@dataclass(frozen=True)
class SubAgent:
    name: str
    responsibility: str
    tools: tuple[str, ...]
    consent_required: bool = False


class MasterOrchestrator:
    """Mission planner for the master/sub-agent architecture."""

    def plan(self, mission_type: str) -> list[SubAgent]:
        if mission_type == "user-registration":
            return [
                SubAgent(
                    name="Identity Registrar",
                    responsibility="Create the user profile and consent record in MongoDB Mission Vault.",
                    tools=("MongoDB Mission Vault",),
                    consent_required=True,
                ),
                SubAgent(
                    name="Context Seeder",
                    responsibility="Attach approved Google, Apple, GitHub, social, travel, shopping, and manual preference sources.",
                    tools=("MongoDB Mission Vault", "OAuth", "Browser Session"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Mission Router",
                    responsibility="Route future requests to gift, flight, account, social, shopping, or DevOps sub-agents.",
                    tools=("Gemini 3", "Arize Observability"),
                ),
            ]

        if mission_type == "mission-router":
            return [
                SubAgent(
                    name="Intent Classifier",
                    responsibility="Classify the user request as gift, flight, account, social, shopping, DevOps, or general task.",
                    tools=("Gemini 3", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Capability Loader",
                    responsibility="Select the lightest useful sub-agents and partner tools for the mission.",
                    tools=("Elastic Action Search", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Oversight Gate",
                    responsibility="Decide where the agent can continue autonomously and where user approval is required.",
                    tools=("Arize Observability",),
                    consent_required=True,
                ),
            ]

        if mission_type == "gift-scout":
            return [
                SubAgent(
                    name="Consent Broker",
                    responsibility="Confirm what friend data the user is allowed to provide.",
                    tools=("MongoDB Mission Vault",),
                    consent_required=True,
                ),
                SubAgent(
                    name="Social Context Scout",
                    responsibility="Read public links, exports, or user-approved browser sessions without storing raw social passwords.",
                    tools=("Browser Session", "Elastic Action Search"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Preference Inference",
                    responsibility="Infer interests, sizes, hobbies, brands, constraints, and confidence levels.",
                    tools=("Gemini 3", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Product Scout",
                    responsibility="Search merchant catalogs and marketplace pages for candidate gifts.",
                    tools=("Browser Session", "Elastic Action Search"),
                ),
                SubAgent(
                    name="Price And Logistics",
                    responsibility="Compare price, shipping speed, taxes, international availability, and seller trust.",
                    tools=("Browser Session", "Fivetran Pipeline"),
                ),
                SubAgent(
                    name="Gift Ranker",
                    responsibility="Rank recommendations by fit, price, delivery confidence, and novelty.",
                    tools=("Gemini 3", "Arize Observability"),
                ),
                SubAgent(
                    name="Checkout Prep",
                    responsibility="Prepare the cart and stop for user confirmation before payment.",
                    tools=("Browser Session", "MongoDB Mission Vault"),
                    consent_required=True,
                ),
            ]

        if mission_type == "shopping-scout":
            return [
                SubAgent(
                    name="Constraint Mapper",
                    responsibility="Turn a vague purchase request into item, budget, region, delivery, and risk constraints.",
                    tools=("Gemini 3", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Product Scout",
                    responsibility="Search merchant catalogs and marketplaces for comparable products.",
                    tools=("Browser Session", "Elastic Action Search"),
                ),
                SubAgent(
                    name="Price And Logistics",
                    responsibility="Compare landed cost, international availability, seller trust, returns, and delivery confidence.",
                    tools=("Browser Session", "Fivetran Pipeline"),
                ),
                SubAgent(
                    name="Checkout Gate",
                    responsibility="Prepare carts or shortlists and stop before payment or irreversible purchase actions.",
                    tools=("Browser Session", "MongoDB Mission Vault"),
                    consent_required=True,
                ),
            ]

        if mission_type == "travel-concierge":
            return [
                SubAgent(
                    name="Travel Constraint Mapper",
                    responsibility="Load home airport, passport, budget, dates, seat, layover, and stay preferences from the Mission Vault.",
                    tools=("Gemini 3", "MongoDB Mission Vault"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Flight Scout",
                    responsibility="Search flight pages, handle autocomplete selection, and compare fare/date windows.",
                    tools=("Browser Session", "Elastic Action Search"),
                ),
                SubAgent(
                    name="Stay Scout",
                    responsibility="Compare hotels and stays, including package timing and cancellation constraints.",
                    tools=("Browser Session", "Elastic Action Search"),
                ),
                SubAgent(
                    name="Price And Logistics",
                    responsibility="Normalize total landed trip cost, baggage, taxes, connections, and arrival/departure friction.",
                    tools=("Fivetran Pipeline", "Arize Observability"),
                ),
                SubAgent(
                    name="Booking Gate",
                    responsibility="Prepare booking details and stop before reservations, payment, or irreversible passenger changes.",
                    tools=("Browser Session", "MongoDB Mission Vault"),
                    consent_required=True,
                ),
            ]

        if mission_type == "social-manager":
            return [
                SubAgent(
                    name="Consent Broker",
                    responsibility="Confirm which social accounts, public links, exports, or browser sessions can be used.",
                    tools=("MongoDB Mission Vault", "OAuth", "Browser Session"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Context Reader",
                    responsibility="Read approved audience, tone, and content-history signals without storing raw social passwords.",
                    tools=("Elastic Action Search", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Content Strategist",
                    responsibility="Draft posts, cadence, variants, and approval checkpoints for the requested campaign.",
                    tools=("Gemini 3", "Arize Observability"),
                ),
                SubAgent(
                    name="Publish Gate",
                    responsibility="Schedule or publish only after explicit user approval.",
                    tools=("Browser Session", "MongoDB Mission Vault"),
                    consent_required=True,
                ),
            ]

        if mission_type == "gitlab-registration":
            return [
                SubAgent(
                    name="Registration Browser",
                    responsibility="Fill GitLab registration fields and detect human checkpoints.",
                    tools=("Browser Session",),
                    consent_required=True,
                ),
                SubAgent(
                    name="GitLab Sync",
                    responsibility="Create the mission repository and sync the audit script.",
                    tools=("GitLab MCP",),
                ),
            ]

        if mission_type == "github-sync":
            return [
                SubAgent(
                    name="Connection Broker",
                    responsibility="Ask the user to connect GitHub through OAuth, a vault-stored token, or browser handoff.",
                    tools=("MongoDB Mission Vault",),
                    consent_required=True,
                ),
                SubAgent(
                    name="Repository Mapper",
                    responsibility="List allowed GitHub repositories and ask which should be synced.",
                    tools=("GitHub API",),
                    consent_required=True,
                ),
                SubAgent(
                    name="GitLab Import Sync",
                    responsibility="Create matching GitLab projects and sync selected repository metadata.",
                    tools=("GitLab MCP",),
                ),
            ]

        if mission_type == "data-context":
            return [
                SubAgent(
                    name="Consent Broker",
                    responsibility="Ask what accounts or files the user wants to connect and what scopes are allowed.",
                    tools=("OAuth", "Browser Session"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Context Normalizer",
                    responsibility="Convert allowed account data into preferences, constraints, contacts, and task history.",
                    tools=("Gemini 3", "MongoDB Mission Vault"),
                ),
                SubAgent(
                    name="Context Auditor",
                    responsibility="Track source, consent, expiry, and deletion controls for each context item.",
                    tools=("MongoDB Mission Vault", "Arize Observability"),
                ),
            ]

        if mission_type == "account-resolver":
            return [
                SubAgent(
                    name="Account Resolver",
                    responsibility="Check whether the user already has an account for the target service.",
                    tools=("MongoDB Mission Vault",),
                    consent_required=True,
                ),
                SubAgent(
                    name="Text DOM Deconstructor",
                    responsibility="Map forms by visible text, accessible names, ARIA roles, and semantic input types.",
                    tools=("Browser Session", "Elastic Action Search"),
                ),
                SubAgent(
                    name="Form Operator",
                    responsibility="Fill visible focused fields with real keyboard and input events.",
                    tools=("Browser Session",),
                    consent_required=True,
                ),
                SubAgent(
                    name="Human Checkpoint Monitor",
                    responsibility="Detect CAPTCHA, MFA, or email verification and pause until the user completes it.",
                    tools=("Browser Session", "Arize Observability"),
                    consent_required=True,
                ),
                SubAgent(
                    name="Session Vault Sync",
                    responsibility="Store non-secret account state and consent metadata for future missions.",
                    tools=("MongoDB Mission Vault",),
                ),
            ]

        return [
            SubAgent(
                name="Mission Planner",
                responsibility="Break the user goal into safe action steps.",
                tools=("Gemini 3",),
            )
        ]


def serialize_agents(agents: list[SubAgent]) -> list[dict[str, object]]:
    return [
        {
            "name": agent.name,
            "responsibility": agent.responsibility,
            "tools": list(agent.tools),
            "consent_required": agent.consent_required,
        }
        for agent in agents
    ]
