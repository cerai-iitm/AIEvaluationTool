# Target Configuration

A **target** is the AI system you want to test. TDMS supports three target types, and each one is reached in a different way:

| Type | How the tool talks to it | What you configure |
|---|---|---|
| `WebApp` | opens the site in a real browser, logs in, types each prompt and reads the reply | URL, login, **selectors** |
| `WhatsApp` | opens WhatsApp Web in a real browser and chats with a contact | URL, **selectors**, a QR-code scan per run |
| `API` | calls a model directly over its API, with no browser | URL and a **model name** (the target name) |

WebApp and WhatsApp targets are tested like a person would: the tool needs to know **which element on the page** to type into, click and read. You tell it with **selectors** (XPath or CSS), configured per target in TDMS. The first parts of this page cover those two types. [API Targets](#api-targets) covers the third, including how to test a model served by Ollama on your own machine.

All of this is done in the TDMS UI. You do not need to edit any configuration file.

## Before You Start

- A TDMS account that can manage targets. See [Authentication And Roles](./authentication_and_roles.md).
- The target's address. For `WebApp` and `WhatsApp` targets, also a **test account** if the site needs a login. Use a dedicated test account, not a personal one: the password is stored on the server in plain text.
- For `WebApp` and `WhatsApp` targets: Google Chrome on your own computer, to inspect the target's pages and find the selectors. `API` targets need no browser and no selectors.

## Step 1: Create The Target

1. In TDMS, open **Targets** and click **Add Target**.
2. On the **General** tab, fill in:

   | Field | What to enter |
   |---|---|
   | Target | A short name **without spaces**, for example `support-bot` (see the note below) |
   | Type | `WebApp` for a website chat, `WhatsApp` for a WhatsApp contact, `API` for a model reached over an API |
   | URL | The address of the chat page, for example `https://chat.example.com` |
   | Domain, Languages | As appropriate for the target |
   | Notes | Required. What the target is and who owns it |

**Name the target without spaces.** TDMS stores the selectors under the name with spaces turned into underscores, while the test runner looks them up with the spaces kept. A name such as `Support Bot` therefore saves correctly but fails at run time. Use lowercase letters, digits and hyphens.

For an `API` target the name has a second job: it is the **model name** sent to the provider. Continue in [API Targets](#api-targets); Steps 2 to 5 below are for `WebApp` and `WhatsApp` targets.

## Step 2: Add The Login Details (WebApp)

If the site needs a login, open the **Credentials** tab and enter the test account's username and password. Leave both empty if the site has no login. If you fill in one field, you must fill in both.

WhatsApp targets have no credentials. They log in by scanning a QR code; see [WhatsApp Targets](#whatsapp-targets).

## Step 3: Configure The Selectors

Open the **XPath Config** tab. It starts with a template for the chosen type, with the selector values left empty for you to fill in.

The configuration is grouped into **pages**, each with its own **fields**:

| Page | Used for | Needed when |
|---|---|---|
| `LoginPage` | filling in and submitting the login form | the site has a login |
| `LogoutPage` | detecting an existing session and logging out | the site has a login |
| `ChatPage` | typing the prompt and reading the reply | always |

How to work with the editor:

- **Add a page:** use the **Add page** button and pick one of the standard pages. Use **Custom page…** only for a page name the tool does not know; it will be ignored unless the code reads it.
- **Add a field:** open the page, then pick a field from its list. Required fields are marked `* required`, and the editor lists the required fields that are still missing.
- **Remove a field:** delete fields you do not need instead of leaving them empty. The target cannot be submitted while any field in the configuration is empty.

### LoginPage Fields

All three are required, and they must be **XPath** selectors.

| Field | Element |
|---|---|
| `email_input_element` | the username or email box |
| `password_input_element` | the password box |
| `login_button_element` | the sign-in button |

### LogoutPage Fields

| Field | Required | Element |
|---|---|---|
| `profile_pic_element` | see note | something that is only visible when logged in, such as the avatar; used to skip the login when a session already exists |
| `profile_element` | see note | the menu or avatar that must be clicked before the sign-out button appears |
| `logout_button_element` | yes | the sign-out button |

The editor marks two of these as optional, but the code reads them whenever a `LogoutPage` exists:

- the login step reads `profile_pic_element`; without it, the login fails;
- the logout step always clicks `profile_element` before `logout_button_element`; without it, the logout fails.

If you add a `LogoutPage`, include all three fields.

### ChatPage Fields

| Field | Required | Element or value |
|---|---|---|
| `prompt_input_box_element` | yes | the box where the prompt is typed |
| `agent_response_element` | yes | the element that contains the reply text |
| `send_button_element` | **yes, see note** | the send button |
| `submit_via_click` | no | `true` to click the send button; otherwise the prompt is sent by pressing Enter |
| `message_in_element`, `message_out_element` | no, as a pair | incoming and outgoing chat bubbles; see [How Replies Are Read](#how-replies-are-read) |
| `shadow_root_element` | no | CSS selector of a shadow-DOM host; see [How Replies Are Read](#how-replies-are-read) |
| `response_timeout` | no | maximum seconds to wait for a reply |
| `response_stable_time` | no | seconds the reply must stop changing before it counts as complete |
| `response_poll_interval` | no | seconds between checks while waiting |
| `pre_send_wait` | no | shadow-DOM mode only: seconds to wait after sending, before checking |

The editor marks `send_button_element` as optional, but the test runner reads it for every prompt of a WebApp target, to check that the chat page is ready. **Always set it.** The WebApp template does not include it, so add it from the field list.

### How Replies Are Read

The fields you set choose how the reply is captured:

| Mode | Set these fields | Use it when |
|---|---|---|
| Single reply element (default) | `agent_response_element` | the reply appears in one element whose text grows until it is complete |
| Chat bubbles | `message_in_element` and `message_out_element` | the page shows a list of sent and received bubbles |
| Shadow DOM | `shadow_root_element` and `agent_response_element` | the chat widget is inside a shadow DOM, so normal selectors cannot reach it |

The timing fields (`response_timeout`, `response_stable_time`, `response_poll_interval`) apply to all modes. Raise them for slow agents.

### XPath Or CSS

A selector that starts with `//`, `(//` or `.//` is treated as XPath. Anything else is treated as a CSS selector. Login fields must be XPath; for other fields either works.

## Step 4: Find And Test Each Selector

Do this in Chrome on the target's real pages: the login page for `LoginPage`, and the chat page **while logged in** for `ChatPage` and `LogoutPage`.

1. Right-click the element (for example the prompt box) and choose **Inspect**. The element is highlighted in the Elements panel.
2. Look for an attribute that is stable and unique: `id`, `name`, `aria-label`, `placeholder`, `data-testid`, `type`, or the button's visible text.
3. Write a short selector based on it, for example:

   ```text
   //textarea[@placeholder='Type a message']
   //button[@aria-label='Send']
   //input[@id='email']
   ```

4. Test it in the **Console** tab:

   ```js
   $x("//button[@aria-label='Send']")
   ```

   For inputs and buttons, the result must be **exactly one** element. Zero means the selector is wrong; more than one means it is not specific enough.
5. For the reply, send a message by hand first, then check that `agent_response_element` matches the element holding the reply text.

Avoid selectors that break easily:

| Avoid | Why |
|---|---|
| Absolute paths such as `/html/body/div[2]/div/div[3]` | break with any layout change |
| Generated class names such as `css-1x2y3z` | change with every release of the site |
| Your own name or other account-specific text | fails for any other account |
| Copying the XPath from **Copy → Copy XPath** unchanged | usually produces an absolute or index-based path |

Check that every selector is well formed before saving: matching brackets and quotes, and `contains(@attr, 'value')` with a comma, not `=`.

## Step 5: Save And Test

1. Click **Submit**. The configuration takes effect immediately for the next run; no restart is needed.
2. In the Test Case Execution Dashboard, start a small run against the target: set **Max test cases** to `1`. See [Run Configuration Manual](./run_configuration_manual.md).
3. Click **View Test Execution** to watch the browser while it runs. You can see which step it stops at: login, typing, sending or reading the reply.
4. Fix the selector for that step, and run again.

## Updating A Target Later

Sites change their pages, and selectors stop working. To update them:

1. Open **Targets**, and edit the target.
2. Open its **XPath Configuration** editor, change the fields, and click **Save**.
3. Run a one-test-case check again.

## WhatsApp Targets

- The **XPath Config** tab starts with the WhatsApp Web template. WhatsApp changes its page from time to time; if runs fail, re-check the `ChatPage` selectors with Step 4.
- The first time a run starts, WhatsApp Web shows a QR code. Open **View Test Execution** and scan it with the phone of the test WhatsApp account. The run waits about **60 seconds** for the scan.
- All test cases of one run share the same browser, so the QR code is scanned once per run.
- WhatsApp limits how many devices one account can link, which limits how many WhatsApp runs can execute at the same time.

## API Targets

An `API` target is a model that the tool calls directly, without a browser. There are no selectors and no login: the **Credentials** and **XPath Configuration** tabs are not needed.

| Field | What to enter |
|---|---|
| Target | The **exact model name** the provider knows, for example `gemma3n:e2b` or `gemini-2.5-flash`. The tool sends this name as the model, and uses it to choose the provider. |
| Type | `API` |
| URL | Where the model is served. For a local model, this is the address of the local server, for example `http://host.docker.internal:11434` |

The tool picks the provider from the URL and the model name:

| Condition | Provider |
|---|---|
| URL starts with `http://localhost`, `http://127.0.0.1` or `http://host.docker.internal` | local model server (Ollama) |
| otherwise, model name starts with `gemini` | Google Gemini |
| otherwise, model name starts with `gpt` or `o` | OpenAI |

For a hosted model such as Gemini, the URL is only a placeholder, and the provider's API key comes from the server's `.env` file. If the model name does not match any of these, the run fails with *Unable to determine provider*.

An API target has no live browser view, so **View Test Execution** is not available for it.

### Testing A Local Ollama Model

Testing a model served by Ollama on the same computer is where most setup problems appear, because the tool runs **inside Docker containers** and Ollama runs **on the host**. Three separate things can block the connection. Work through them in order.

#### 1. Use the host's address, not `localhost`

Inside a container, `localhost` is the container itself, not your computer, so a target URL of `http://localhost:11434` fails even though Ollama is running.

Set the target URL to:

```text
http://host.docker.internal:11434
```

The `app-backend` and `interface-manager` services already map this name to the host through `extra_hosts: host.docker.internal:host-gateway` in `docker-compose.yml`, so it resolves with no further setup. A URL that starts with `http://host.docker.internal` is also recognized as a local model.

#### 2. Make Ollama listen on more than the loopback address

By default Ollama listens on `127.0.0.1:11434` only. A request that arrives from the Docker network is then **refused**, even though Ollama works fine from the host.

Check what it listens on:

```bash
ss -ltnp | grep 11434
```

`127.0.0.1:11434` is the problem; `*:11434` or `0.0.0.0:11434` is what you need. Ollama installed as a systemd service is changed with an override file:

```bash
sudo systemctl edit ollama.service
```

In the editor that opens, add these lines **above the comment markers**, then save and exit:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

Then repeat the `ss` check. Common mistakes:

- **The override was never saved.** If the editor is closed without saving properly, a hidden temporary file such as `/etc/systemd/system/ollama.service.d/.#override.conf…` is left behind and nothing changes. Confirm that `/etc/systemd/system/ollama.service.d/override.conf` exists and contains the lines above. You can also create it by hand with `sudo` and run `daemon-reload` afterwards.
- **`restart` was skipped.** `daemon-reload` only reads the file; Ollama keeps listening on the old address until it is restarted.
- **Ollama was started with `ollama serve` in a terminal.** The systemd override does not apply. Start it with `OLLAMA_HOST=0.0.0.0 ollama serve` instead.

#### 3. Allow the Docker network through the firewall

If the host firewall (`ufw`) blocks incoming traffic by default, requests from containers are **dropped silently**. The symptom differs from step 2: the run **times out** instead of being refused immediately.

Check the firewall and find the Docker subnets:

```bash
sudo ufw status
docker network ls
docker network inspect <network-name> --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
```

Allow each subnet to reach the Ollama port. For example, for the default bridge and the Compose network:

```bash
sudo ufw allow from 172.17.0.0/16 to any port 11434
sudo ufw allow from 172.19.0.0/16 to any port 11434
```

`172.17.0.0/16` is the default Docker bridge. The Compose network's subnet depends on your machine, so use the value from `docker network inspect`, not the one above. Allowing only the Docker subnets keeps Ollama closed to the rest of the network, which matters because `OLLAMA_HOST=0.0.0.0` otherwise makes it reachable from other computers.

#### Check The Connection

From a container, ask Ollama for its model list. Use a container on the Compose network, such as `interface-manager`, and the same address as the target URL (`curl` must be available in that container):

```bash
docker compose exec interface-manager curl http://host.docker.internal:11434/api/tags
```

If it returns your models as JSON, the target will work. Then check that the target name matches one of the listed models **exactly**, including the tag (`gemma3n:e2b`, not `gemma3n`), and run one test case as described in [Step 5](#step-5-save-and-test).

#### What The Symptom Tells You

| What you see | Likely cause | Fix |
|---|---|---|
| Connection refused, immediately | Ollama listens on `127.0.0.1` only, or the URL uses `localhost` | step 2, or step 1 |
| Name `host.docker.internal` not resolved | the container has no `extra_hosts` entry for it | add `host.docker.internal:host-gateway` to the service in `docker-compose.yml` |
| Timeout after a long wait | the firewall drops container traffic | step 3 |
| Connection works but the run returns no response or an error from Ollama | the target name is not an installed model name | run `ollama list` and use the exact name |
| *Unable to determine provider* | the URL does not start with `http://localhost`, `http://127.0.0.1` or `http://host.docker.internal`, and the model name is not a Gemini or OpenAI name | use one of those URL forms |

## Related Pages

- [TDMS Dashboard Manual: Managing Targets](./tdms_dashboard_manual.md#managing-targets)
- [Run Configuration Manual](./run_configuration_manual.md)
- [Troubleshooting: Web App And WhatsApp Targets](./troubleshooting.md#web-app-and-whatsapp-targets)
