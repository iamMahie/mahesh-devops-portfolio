(() => {
  "use strict";

  const main = document.getElementById("main");
  if (!main?.dataset.section) return;
  const section = main.dataset.section;
  const prefix = main.dataset.api;
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const feedback = document.getElementById("workspace-feedback");
  const endpoint = { inquiries: "/inquiries", bookings: "/bookings", messages: "/contact/messages", portfolios: "/portfolios" };
  const transitions = {
    inquiries: { new: ["contacted", "lost"], contacted: ["quoted", "lost"], quoted: ["won", "lost"], won: [], lost: [] },
    bookings: { pending: ["confirmed", "cancelled"], confirmed: ["completed", "cancelled"], completed: [], cancelled: [] }
  };
  let page = 1;
  let pages = 0;
  let loadVersion = 0;
  let editorVersion = 0;
  let selectedId = null;
  let deleting = false;
  const label = value => String(value ?? "").replaceAll("_", " ").replace(/\b\w/g, char => char.toUpperCase());
  const plural = (count, singular, multiple) => count === 1 ? singular : multiple;

  function el(tag, text, className) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null) node.textContent = String(text);
    if (className) node.className = className;
    return node;
  }

  function notice(target, message, error = false) {
    target.textContent = message;
    target.className = `admin-notice ${error ? "admin-error" : "admin-success"}`;
    target.setAttribute("role", error ? "alert" : "status");
    target.hidden = !message;
  }

  async function api(path, options = {}) {
    const headers = { Accept: "application/json", ...options.headers };
    if (options.method && options.method !== "GET") headers["X-CSRF-Token"] = csrf;
    if (options.body !== undefined) headers["Content-Type"] = "application/json";
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    let response;
    try {
      response = await fetch(`${prefix}${path}`, { ...options, headers, signal: controller.signal, credentials: "same-origin", cache: "no-store" });
    } catch {
      if (controller.signal.aborted) {
        throw new Error("The studio took too long to respond. Refresh the records to check whether your change was saved before trying again.");
      }
      throw new Error("Could not reach the studio. Check your connection and try again. Your entered values are still here.");
    } finally {
      window.clearTimeout(timeout);
    }
    if (response.status === 401) {
      window.location.assign("/admin/login");
      throw new Error("Your session has expired. Please sign in again.");
    }
    if (response.status === 204) return null;
    let body;
    try {
      body = await response.json();
    } catch {
      throw new Error("The server returned an unexpected response. Refresh and try again.");
    }
    if (!response.ok) {
      const errors = body.error?.details?.errors;
      const details = Array.isArray(errors) ? errors.map(item => `${label(item.loc?.at(-1) || "Field")}: ${item.msg}`).join(" ") : "";
      throw new Error(details || body.error?.message || `The request could not be completed (${response.status}). Try again.`);
    }
    return body;
  }

  async function run(button, action, target = feedback) {
    if (button?.disabled) return;
    if (button) {
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
    }
    try {
      await action();
    } catch (error) {
      notice(target, error.message || "The change could not be saved. Please try again.", true);
    } finally {
      if (button) {
        button.disabled = false;
        button.removeAttribute("aria-busy");
      }
    }
  }

  function actionButton(text, action, className = "admin-button admin-secondary", target = feedback) {
    const button = el("button", text, className);
    button.type = "button";
    button.addEventListener("click", () => { void run(button, action, target); });
    return button;
  }

  function safeImageURL(value) {
    if (!value) return null;
    try {
      const url = new URL(value, window.location.origin);
      return ["https:", "http:"].includes(url.protocol) ? url.href : null;
    } catch {
      return null;
    }
  }

  function dateText(value, includeTime = false) {
    if (!value) return "Not provided";
    const date = new Date(includeTime ? value : `${value.slice(0, 10)}T12:00:00`);
    if (Number.isNaN(date.getTime())) return String(value);
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium", ...(includeTime ? { timeStyle: "short" } : {})
    }).format(date);
  }

  const menu = document.getElementById("admin-menu");
  const sidebar = document.querySelector(".admin-sidebar");
  const mobile = window.matchMedia("(max-width: 760px)");
  function updateMenu() {
    menu.hidden = !mobile.matches;
    sidebar.classList.toggle("admin-nav-collapsed", mobile.matches);
    menu.setAttribute("aria-expanded", String(!mobile.matches));
  }
  updateMenu();
  mobile.addEventListener("change", updateMenu);
  menu.addEventListener("click", () => {
    const expanded = menu.getAttribute("aria-expanded") !== "true";
    sidebar.classList.toggle("admin-nav-collapsed", !expanded);
    menu.setAttribute("aria-expanded", String(expanded));
  });

  function confirmDelete(description) {
    const dialog = document.getElementById("delete-dialog");
    document.getElementById("delete-description").textContent = description;
    dialog.returnValue = "";
    return new Promise(resolve => {
      dialog.addEventListener("close", () => resolve(dialog.returnValue === "delete"), { once: true });
      dialog.showModal();
    });
  }
  document.getElementById("cancel-delete").addEventListener("click", () => document.getElementById("delete-dialog").close("cancel"));
  document.getElementById("confirm-delete").addEventListener("click", () => document.getElementById("delete-dialog").close("delete"));

  async function overview() {
    const container = document.getElementById("overview-counts");
    container.setAttribute("aria-busy", "true");
    container.replaceChildren(el("p", "Loading studio activity…"));
    const metrics = [
      { title: "New enquiries", path: "/inquiries", query: "status=new", link: "/admin/inquiries?status=new", singular: "enquiry", plural: "enquiries" },
      { title: "Pending consultations", path: "/bookings", query: "status=pending", link: "/admin/bookings?status=pending", singular: "consultation", plural: "consultations" },
      { title: "Unread messages", path: "/contact/messages", query: "is_read=false", link: "/admin/messages?is_read=false", singular: "message", plural: "messages" },
      { title: "Featured portfolios", path: "/portfolios", query: "is_featured=true", link: "/admin/portfolios?is_featured=true", singular: "portfolio", plural: "portfolios" }
    ];
    try {
      const data = await Promise.all(metrics.map(async metric => {
        const [filtered, all] = await Promise.all([
          api(`${metric.path}?size=1&${metric.query}`), api(`${metric.path}?size=1`)
        ]);
        return { metric, count: filtered.total, total: all.total };
      }));
      container.replaceChildren(...data.map(({ metric, count, total }) => {
        const link = el("a");
        link.href = metric.link;
        const description = el("span", metric.title);
        description.append(el("small", `${total.toLocaleString()} ${plural(total, metric.singular, metric.plural)} in total`));
        link.append(description, el("strong", count.toLocaleString()));
        return link;
      }));
      notice(feedback, "");
    } catch (error) {
      container.replaceChildren(el("p", "Activity is unavailable. Use Refresh to try again."));
      throw error;
    } finally {
      container.setAttribute("aria-busy", "false");
    }
  }

  if (section === "overview") {
    const refresh = document.getElementById("refresh-overview");
    refresh.addEventListener("click", () => { void run(refresh, overview); });
    void run(refresh, overview);
    return;
  }

  const filters = document.getElementById("record-filters");
  const records = document.getElementById("records");
  const summary = document.getElementById("records-summary");
  const previous = document.getElementById("previous-page");
  const next = document.getElementById("next-page");
  const editor = document.getElementById("record-editor");
  const editorContent = document.getElementById("editor-content");
  const editorFeedback = document.getElementById("editor-feedback");
  const editorHeading = document.getElementById("editor-heading");

  const initialQuery = new URLSearchParams(window.location.search);
  for (const field of filters.elements) {
    if (field.name && initialQuery.has(field.name)) field.value = initialQuery.get(field.name);
  }

  function closeEditor() {
    editorVersion += 1;
    editor.hidden = true;
    selectedId = null;
    editorContent.replaceChildren();
    const trigger = records.querySelector(`[data-record-id="${CSS.escape(String(editor.dataset.recordId || ""))}"]`);
    (trigger || document.getElementById("create-portfolio") || document.getElementById("refresh-records")).focus();
  }
  document.getElementById("close-editor").addEventListener("click", closeEditor);

  function prepareEditor(id, title) {
    editorVersion += 1;
    selectedId = id;
    editor.dataset.recordId = id ?? "";
    editorHeading.textContent = title;
    editorContent.replaceChildren();
    notice(editorFeedback, "");
    editor.hidden = false;
    editorHeading.focus();
    editor.scrollIntoView({ block: "start", behavior: "instant" });
    return editorVersion;
  }

  function statusBadge(record) {
    const value = section === "messages" ? (record.is_read ? "read" : "unread") : section === "portfolios" ? (record.is_featured ? "featured" : "not featured") : record.status;
    const badge = el("span", label(value), "admin-status");
    badge.dataset.status = value;
    return badge;
  }

  function tableRow(record) {
    const row = el("tr");
    const primary = el("td");
    primary.append(el("strong", record.title || record.customer_name || record.name));
    primary.append(el("small", record.email || label(record.category)));
    const detail = el("td", section === "inquiries" ? dateText(record.event_date) : section === "bookings" ? dateText(record.booking_date) : section === "messages" ? record.subject : `/${record.slug}`);
    const status = el("td");
    status.append(statusBadge(record));
    const date = el("td", dateText(record.created_at, false));
    const actions = el("td");
    const open = actionButton(section === "portfolios" ? "Edit & gallery" : "View details", () => openRecord(record));
    open.dataset.recordId = record.id;
    open.setAttribute("aria-label", `${open.textContent}: ${record.title || record.customer_name || record.name}`);
    actions.append(open);
    row.append(primary, detail, status, date, actions);
    return row;
  }

  async function loadRecords() {
    const version = ++loadVersion;
    const query = new URLSearchParams();
    for (const [key, value] of new FormData(filters)) if (String(value).trim()) query.set(key, String(value).trim());
    const visibleQuery = query.toString();
    window.history.replaceState(null, "", `${window.location.pathname}${visibleQuery ? `?${visibleQuery}` : ""}`);
    query.set("page", page);
    query.set("size", main.dataset.pageSize);
    records.setAttribute("aria-busy", "true");
    summary.textContent = "Loading records…";
    previous.disabled = true;
    next.disabled = true;
    try {
      const result = await api(`${endpoint[section]}?${query}`);
      if (version !== loadVersion) return;
      pages = result.pages;
      if (page > pages && page > 1) {
        page = Math.max(1, pages);
        await loadRecords();
        return;
      }
      const noun = section === "inquiries" ? "enquiries" : section === "bookings" ? "consultations" : section;
      const singular = { inquiries: "enquiry", bookings: "consultation", messages: "message", portfolios: "portfolio" }[section];
      summary.textContent = `${result.total.toLocaleString()} ${plural(result.total, singular, noun)}${visibleQuery ? " matching your filters" : ""}.`;
      if (!result.items.length) {
        const empty = el("div", null, "admin-empty");
        empty.append(el("h3", visibleQuery ? "No matching records." : `No ${noun} yet.`));
        empty.append(el("p", visibleQuery ? "Try a different search or reset your filters." : section === "portfolios" ? "Create a portfolio to publish a collection of your work." : "New customer submissions will appear here. Use Refresh to check again."));
        records.replaceChildren(empty);
      } else {
        const scroll = el("div", null, "admin-table-scroll");
        scroll.tabIndex = 0;
        scroll.setAttribute("role", "region");
        scroll.setAttribute("aria-label", `${label(noun)} records; scroll horizontally for all columns`);
        const table = el("table", null, "admin-table");
        const caption = el("caption", `${label(noun)} records`, "sr-only");
        const head = el("thead");
        const tr = el("tr");
        const headers = [section === "portfolios" ? "Portfolio" : "Customer", section === "inquiries" ? "Event date" : section === "bookings" ? "Requested date" : section === "messages" ? "Subject" : "Page address", "Status", "Received", "Actions"];
        if (section === "portfolios") headers[3] = "Published";
        headers.forEach(text => { const th = el("th", text); th.scope = "col"; tr.append(th); });
        head.append(tr);
        const body = el("tbody");
        body.append(...result.items.map(tableRow));
        table.append(caption, head, body);
        scroll.append(table);
        records.replaceChildren(scroll);
      }
      document.getElementById("page-label").textContent = pages ? `Page ${page} of ${pages}` : "No pages";
      previous.disabled = page <= 1;
      next.disabled = page >= pages;
    } catch (error) {
      if (version !== loadVersion) return;
      records.replaceChildren(el("p", "Records could not be loaded. Use Refresh to try again.", "admin-empty"));
      summary.textContent = "Records unavailable.";
      document.getElementById("page-label").textContent = "";
      throw error;
    } finally {
      if (version === loadVersion) records.setAttribute("aria-busy", "false");
    }
  }

  async function refreshAfterSave() {
    try {
      await loadRecords();
    } catch (error) {
      notice(feedback, `Your change was saved, but the list could not refresh. ${error.message}`, true);
    }
  }

  filters.addEventListener("submit", event => {
    event.preventDefault();
    page = 1;
    notice(feedback, "");
    void run(event.submitter, loadRecords);
  });
  filters.addEventListener("reset", () => {
    window.setTimeout(() => {
      page = 1;
      notice(feedback, "");
      void run(null, loadRecords);
    }, 0);
  });
  previous.addEventListener("click", () => {
    if (page <= 1) return;
    page -= 1;
    void run(null, loadRecords);
  });
  next.addEventListener("click", () => {
    if (page >= pages) return;
    page += 1;
    void run(null, loadRecords);
  });
  const refresh = document.getElementById("refresh-records");
  refresh.addEventListener("click", () => {
    notice(feedback, "");
    void run(refresh, loadRecords);
  });

  function addDetail(list, name, value, wide = false) {
    const item = el("div", null, wide ? "admin-detail-wide" : "");
    item.append(el("dt", name), el("dd", value || "Not provided"));
    list.append(item);
  }

  async function deleteRecord(record) {
    if (deleting) return;
    deleting = true;
    try {
      const name = record.title || record.customer_name || record.name;
      const extra = section === "portfolios" ? " Its gallery records will also be deleted. The public portfolio page will no longer exist." : "";
      if (!await confirmDelete(`Delete “${name}”?${extra}`)) return;
      await api(`${endpoint[section]}/${record.id}`, { method: "DELETE" });
      closeEditor();
      notice(feedback, "Record deleted.");
      await refreshAfterSave();
    } finally {
      deleting = false;
    }
  }

  function showRecord(record) {
    editorContent.replaceChildren();
    const details = el("dl", null, "admin-details");
    addDetail(details, "Customer", record.customer_name || record.name);
    addDetail(details, "Email", record.email);
    if (section === "inquiries") {
      addDetail(details, "Phone", record.phone);
      addDetail(details, "Event date", dateText(record.event_date));
      addDetail(details, "Location", record.location);
      addDetail(details, "Package interest", label(record.package_interest));
      addDetail(details, "Message", record.message, true);
    } else if (section === "bookings") {
      addDetail(details, "Requested consultation date", dateText(record.booking_date));
      addDetail(details, "Notes", record.notes, true);
    } else {
      addDetail(details, "Subject", record.subject, true);
      addDetail(details, "Message", record.message, true);
    }
    addDetail(details, "Received", dateText(record.created_at, true));
    const status = el("p", "Current status: ");
    status.append(statusBadge(record));
    const actions = el("div", null, "admin-record-actions");
    if (section === "messages") {
      actions.append(actionButton(record.is_read ? "Mark unread" : "Mark read", async () => {
        const updated = await api(`${endpoint[section]}/${record.id}/read?is_read=${!record.is_read}`, { method: "PATCH" });
        if (selectedId === record.id) showRecord(updated);
        notice(editorFeedback, updated.is_read ? "Message marked read." : "Message marked unread.");
        await refreshAfterSave();
      }, "admin-button", editorFeedback));
    } else {
      const allowed = transitions[section][record.status] || [];
      if (allowed.length) {
        const form = el("form");
        const field = el("div", null, "admin-field");
        const select = el("select");
        select.id = "next-status";
        select.required = true;
        const placeholder = el("option", "Choose a new status");
        placeholder.value = "";
        select.append(placeholder);
        allowed.forEach(value => {
          const option = el("option", label(value));
          option.value = value;
          select.append(option);
        });
        const title = el("label", "Move conversation to");
        title.htmlFor = select.id;
        field.append(title, select);
        const submit = el("button", "Update status", "admin-button");
        submit.type = "submit";
        form.append(field, submit);
        form.addEventListener("submit", event => {
          event.preventDefault();
          void run(submit, async () => {
            const updated = await api(`${endpoint[section]}/${record.id}/status`, { method: "PATCH", body: JSON.stringify({ status: select.value }) });
            if (selectedId === record.id) showRecord(updated);
            notice(editorFeedback, `Status updated to ${label(updated.status)}.`);
            await refreshAfterSave();
          }, editorFeedback);
        });
        actions.append(form);
      } else {
        actions.append(el("p", "This conversation is closed. No further status changes are available.", "admin-help"));
      }
    }
    const deletion = actionButton("Delete record", () => deleteRecord(record), "admin-button admin-secondary", editorFeedback);
    const actionGroup = el("div", null, "admin-actions");
    actionGroup.append(deletion);
    actions.append(actionGroup);
    editorContent.append(status, details, actions);
  }

  async function openRecord(row) {
    const version = prepareEditor(row.id, section === "portfolios" ? "Edit portfolio" : "Conversation details");
    editorContent.append(el("p", "Loading details…"));
    try {
      // Contact's list response contains the complete message; there is no detail endpoint.
      const record = section === "messages" ? row : await api(`${endpoint[section]}/${row.id}`);
      if (version !== editorVersion) return;
      if (section === "portfolios") showPortfolio(record);
      else showRecord(record);
    } catch (error) {
      if (version !== editorVersion) return;
      editorContent.replaceChildren(el("p", "Details are unavailable. Close this panel and try opening the record again."));
      notice(editorFeedback, error.message, true);
    }
  }

  function inputField(name, text, value, { type = "text", required = false, maxLength, min, max } = {}) {
    const wrapper = el("div", null, "admin-field");
    const input = el("input");
    input.name = name;
    input.id = name;
    input.type = type;
    input.value = value ?? "";
    input.required = required;
    if (maxLength) input.maxLength = maxLength;
    if (min !== undefined) input.min = min;
    if (max !== undefined) input.max = max;
    const title = el("label", text);
    title.htmlFor = input.id;
    wrapper.append(title, input);
    return { wrapper, input };
  }

  function imageFields(image, key) {
    const grid = el("div", null, "admin-image-fields");
    const url = inputField(`image-url-${key}`, "Image URL", image.image_url, { required: true, maxLength: 500 });
    const title = inputField(`image-title-${key}`, "Caption / description (optional)", image.title, { maxLength: 200 });
    const order = inputField(`image-order-${key}`, "Order", image.display_order ?? 0, { type: "number", required: true, min: 0, max: 10000 });
    order.input.step = "1";
    grid.append(url.wrapper, title.wrapper, order.wrapper);
    return { grid, payload: () => ({ image_url: url.input.value.trim(), title: title.input.value.trim() || null, display_order: Number(order.input.value) }) };
  }

  async function refreshGallery(portfolioId, container) {
    const images = await api(`/portfolios/${portfolioId}/images`);
    if (selectedId === portfolioId && container.isConnected) renderImages(portfolioId, container, images);
  }

  function renderImages(portfolioId, container, images) {
    container.replaceChildren();
    if (!images.length) container.append(el("p", "No gallery images yet. Add the first photograph below.", "admin-help"));
    for (const image of images) {
      const row = el("div", null, "admin-image-entry");
      const preview = el("img");
      const source = safeImageURL(image.image_url);
      if (source) preview.src = source;
      preview.alt = image.title || "Gallery photograph";
      preview.loading = "lazy";
      preview.referrerPolicy = "no-referrer";
      preview.addEventListener("error", () => {
        preview.replaceWith(el("p", "Preview unavailable. Check the image URL.", "admin-help"));
      }, { once: true });
      const form = el("form");
      const fields = imageFields(image, image.id);
      const localFeedback = el("div", null, "admin-notice");
      localFeedback.setAttribute("aria-live", "polite");
      localFeedback.hidden = true;
      const controls = el("div", null, "admin-actions");
      const save = el("button", "Save image", "admin-button admin-secondary");
      save.type = "submit";
      const cover = actionButton("Use as cover", async () => {
        await api(`/portfolios/${portfolioId}/images/${image.id}/feature`, { method: "PUT" });
        if (selectedId === portfolioId) document.getElementById("portfolio-cover").value = image.image_url;
        notice(localFeedback, "Portfolio cover updated.");
        await refreshAfterSave();
      }, "admin-button admin-secondary", localFeedback);
      const remove = actionButton("Delete image", async () => {
        if (deleting) return;
        deleting = true;
        try {
          if (!await confirmDelete(`Remove “${image.title || "this photograph"}” from the gallery? The source image file will not be deleted.`)) return;
          await api(`/images/${image.id}`, { method: "DELETE" });
          try {
            await refreshGallery(portfolioId, container);
            notice(editorFeedback, "Gallery image deleted.");
          } catch (error) {
            notice(localFeedback, `Image deleted, but the gallery could not refresh. Reopen this portfolio. ${error.message}`, true);
          }
        } finally {
          deleting = false;
        }
      }, "admin-button admin-secondary", localFeedback);
      controls.append(save, cover, remove);
      form.append(fields.grid, controls, localFeedback);
      form.addEventListener("submit", event => {
        event.preventDefault();
        void run(save, async () => {
          const updated = await api(`/images/${image.id}`, { method: "PATCH", body: JSON.stringify(fields.payload()) });
          Object.assign(image, updated);
          const updatedURL = safeImageURL(image.image_url);
          if (updatedURL && preview.isConnected) preview.src = updatedURL;
          if (preview.isConnected) preview.alt = image.title || "Gallery photograph";
          notice(localFeedback, "Image saved. Reopen the portfolio to see the gallery in its updated order.");
        }, localFeedback);
      });
      row.append(preview, form);
      container.append(row);
    }
  }

  function showPortfolio(record = null) {
    selectedId = record?.id ?? null;
    editor.dataset.recordId = selectedId ?? "";
    editorHeading.textContent = record ? `Edit: ${record.title}` : "New portfolio";
    editorContent.replaceChildren(document.getElementById("portfolio-form-template").content.cloneNode(true));
    const form = document.getElementById("portfolio-form");
    if (record) {
      for (const name of ["title", "slug", "category", "description", "cover_image_url"]) form.elements[name].value = record[name] ?? "";
      form.elements.is_featured.checked = record.is_featured;
      form.elements.slug.required = true;
      const publicLink = document.getElementById("portfolio-public-link");
      publicLink.href = `/portfolios/${encodeURIComponent(record.slug)}`;
      publicLink.hidden = false;
    }
    form.addEventListener("submit", event => {
      event.preventDefault();
      void run(event.submitter, async () => {
        const data = {
          title: form.elements.title.value.trim(), category: form.elements.category.value,
          description: form.elements.description.value.trim() || null,
          cover_image_url: form.elements.cover_image_url.value.trim() || null,
          is_featured: form.elements.is_featured.checked
        };
        if (form.elements.slug.value.trim()) data.slug = form.elements.slug.value.trim();
        const version = editorVersion;
        const saved = await api(record ? `/portfolios/${record.id}` : "/portfolios", {
          method: record ? "PATCH" : "POST", body: JSON.stringify(data)
        });
        if (version === editorVersion) {
          showPortfolio(saved);
          notice(editorFeedback, "Portfolio saved and published. You can manage gallery images below.");
          editorHeading.focus();
        }
        await refreshAfterSave();
      }, editorFeedback);
    });
    if (!record) {
      editorContent.append(el("p", "Save the portfolio first, then add gallery images. Saving publishes the collection immediately.", "admin-help"));
      return;
    }
    const gallery = el("section", null, "admin-gallery");
    const heading = el("h3", "Gallery photographs");
    gallery.append(heading, el("p", "Link to your own photographs using HTTPS URLs or local /static/ paths. Lower order numbers appear first. These actions save immediately.", "admin-help"));
    const imageList = el("div");
    renderImages(record.id, imageList, record.images || []);
    gallery.append(imageList);
    const add = el("form", null, "admin-add-image");
    add.append(el("h3", "Add a photograph"));
    const fields = imageFields({ display_order: Math.min(10000, Math.max(0, ...(record.images || []).map(image => image.display_order)) + 1) }, "new");
    const addFeedback = el("div", null, "admin-notice");
    addFeedback.hidden = true;
    addFeedback.setAttribute("aria-live", "polite");
    const submit = el("button", "Add image", "admin-button");
    submit.type = "submit";
    add.append(fields.grid, el("br"), submit, addFeedback);
    add.addEventListener("submit", event => {
      event.preventDefault();
      void run(submit, async () => {
        await api(`/portfolios/${record.id}/images`, {
          method: "POST", body: JSON.stringify({ ...fields.payload(), portfolio_id: record.id })
        });
        add.reset();
        try {
          await refreshGallery(record.id, imageList);
          notice(addFeedback, "Photograph added to the gallery.");
        } catch (error) {
          notice(addFeedback, `Photograph added, but the gallery could not refresh. Reopen this portfolio; do not add it again. ${error.message}`, true);
        }
      }, addFeedback);
    });
    gallery.append(add);
    editorContent.append(gallery);
    const danger = el("div", null, "admin-record-actions");
    danger.append(actionButton("Delete portfolio", () => deleteRecord(record), "admin-button admin-secondary", editorFeedback));
    editorContent.append(danger);
  }

  document.getElementById("create-portfolio")?.addEventListener("click", () => {
    prepareEditor(null, "New portfolio");
    showPortfolio();
    document.getElementById("portfolio-title").focus();
  });
  void run(refresh, loadRecords);
})();
