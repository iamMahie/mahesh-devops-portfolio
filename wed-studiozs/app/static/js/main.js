"use strict";

document.documentElement.classList.add("js-enabled");
const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#navigation");
if (menuButton && navigation) {
  menuButton.hidden = false;
  const closeMenu = () => {
    navigation.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
  };
  menuButton.addEventListener("click", () => {
    const expanded = menuButton.getAttribute("aria-expanded") !== "true";
    menuButton.setAttribute("aria-expanded", String(expanded));
    navigation.classList.toggle("is-open", expanded);
  });
  navigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) closeMenu();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && navigation.classList.contains("is-open")) {
      closeMenu();
      menuButton.focus();
    }
  });
}

const lightbox = document.querySelector("#lightbox");
const photos = Array.from(document.querySelectorAll("a[data-lightbox]"));
if (lightbox && photos.length && typeof lightbox.showModal === "function") {
  const preview = document.createElement("img");
  lightbox.querySelector("#lightbox-stage").append(preview);
  const caption = lightbox.querySelector("#lightbox-caption");
  const count = lightbox.querySelector("#lightbox-count");
  const previous = lightbox.querySelector("[data-previous-image]");
  const next = lightbox.querySelector("[data-next-image]");
  let selected = 0;
  let opener = null;
  const showImage = (index) => {
    selected = (index + photos.length) % photos.length;
    const photo = photos[selected];
    preview.src = photo.href;
    preview.alt = photo.querySelector("img").alt;
    caption.textContent = photo.dataset.caption || preview.alt;
    count.textContent = `${selected + 1} / ${photos.length}`;
    previous.hidden = next.hidden = photos.length < 2;
  };
  photos.forEach((photo, index) => photo.addEventListener("click", (event) => {
    event.preventDefault();
    opener = photo;
    showImage(index);
    lightbox.showModal();
    document.body.classList.add("dialog-open");
  }));
  previous.addEventListener("click", () => showImage(selected - 1));
  next.addEventListener("click", () => showImage(selected + 1));
  lightbox.querySelector("[data-close-lightbox]").addEventListener("click", () => lightbox.close());
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) {
      const bounds = lightbox.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right ||
          event.clientY < bounds.top || event.clientY > bounds.bottom) lightbox.close();
    }
  });
  lightbox.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      showImage(selected + (event.key === "ArrowRight" ? 1 : -1));
    }
  });
  lightbox.addEventListener("close", () => {
    document.body.classList.remove("dialog-open");
    opener?.focus();
  });
}

document.querySelectorAll("form[data-submit-label]").forEach((form) => {
  const submit = form.querySelector('button[type="submit"]');
  if (!submit) return;
  const original = submit.textContent;
  form.addEventListener("submit", () => {
    submit.disabled = true;
    submit.textContent = form.dataset.submitLabel;
    form.setAttribute("aria-busy", "true");
  });
  window.addEventListener("pageshow", () => {
    submit.disabled = false;
    submit.textContent = original;
    form.removeAttribute("aria-busy");
  });
});

const errorSummary = document.querySelector("#form-errors");
if (errorSummary) errorSummary.focus();
