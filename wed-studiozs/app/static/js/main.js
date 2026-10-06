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

(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const scene = document.querySelector("[data-depth-scene]");
  const motionButton = document.querySelector("[data-motion-toggle]");
  let pausedMotion = reducedMotion.matches;
  let frame = 0;
  const resetDepth = () => {
    window.cancelAnimationFrame(frame);
    scene?.style.removeProperty("--tilt-x");
    scene?.style.removeProperty("--tilt-y");
  };
  const syncMotion = () => {
    document.documentElement.classList.toggle("motion-paused", pausedMotion);
    if (motionButton) {
      motionButton.hidden = !finePointer.matches || reducedMotion.matches;
      motionButton.textContent = pausedMotion ? "Enable motion" : "Pause motion";
      motionButton.setAttribute("aria-pressed", String(pausedMotion));
    }
    resetDepth();
  };
  syncMotion();
  motionButton?.addEventListener("click", () => {
    pausedMotion = !pausedMotion;
    syncMotion();
  });
  scene?.addEventListener("pointermove", (event) => {
    if (pausedMotion || reducedMotion.matches || !finePointer.matches || event.pointerType === "touch") return;
    const bounds = scene.getBoundingClientRect();
    const x = (event.clientX - bounds.left) / bounds.width - .5;
    const y = (event.clientY - bounds.top) / bounds.height - .5;
    window.cancelAnimationFrame(frame);
    frame = window.requestAnimationFrame(() => {
      scene.style.setProperty("--tilt-x", `${-y * 7}deg`);
      scene.style.setProperty("--tilt-y", `${x * 12}deg`);
    });
  });
  scene?.addEventListener("pointerleave", resetDepth);

  const players = [];
  document.querySelectorAll("[data-reel]").forEach((card) => {
    const video = card.querySelector("video");
    const controls = card.querySelector(".reel-controls");
    const play = card.querySelector("[data-play]");
    const sound = card.querySelector("[data-sound]");
    const captions = card.querySelector("[data-captions]");
    const status = card.querySelector(".reel-status");
    const title = card.querySelector("h3").textContent;
    let wantsPlayback = false;
    let attempt = 0;
    let showCaptions = false;

    video.muted = true;
    const sync = () => {
      play.textContent = video.paused ? "Play" : "Pause";
      play.setAttribute("aria-label", `${video.paused ? "Play" : "Pause"} ${title}`);
      sound.textContent = video.muted ? "Unmute" : "Mute";
      sound.setAttribute("aria-label", `${video.muted ? "Unmute" : "Mute"} ${title}`);
      sound.setAttribute("aria-pressed", String(!video.muted));
      card.classList.toggle("is-playing", !video.paused);
    };
    const pause = () => {
      wantsPlayback = false;
      attempt += 1;
      video.pause();
      video.muted = true;
      card.removeAttribute("aria-busy");
      sync();
    };
    const start = async (automatic = false) => {
      if (document.hidden || (automatic && (reducedMotion.matches || !finePointer.matches))) return;
      players.forEach(player => { if (player.card !== card) player.pause(); });
      wantsPlayback = true;
      const currentAttempt = ++attempt;
      if (automatic) video.muted = true;
      status.textContent = "";
      card.setAttribute("aria-busy", "true");
      try {
        await video.play();
        if (!wantsPlayback) video.pause();
      } catch (error) {
        if (currentAttempt !== attempt || !wantsPlayback) return;
        wantsPlayback = false;
        status.textContent = error.name === "NotAllowedError"
          ? "Your browser paused the preview. Tap Play to watch."
          : "This film could not play. Try Play again, or use Open film.";
      } finally {
        if (currentAttempt === attempt) {
          card.removeAttribute("aria-busy");
          sync();
        }
      }
    };
    play.addEventListener("click", () => {
      if (wantsPlayback || !video.paused) pause();
      else void start();
    });
    sound.addEventListener("click", () => { video.muted = !video.muted; });
    card.addEventListener("pointerenter", (event) => {
      if (event.pointerType !== "touch" && finePointer.matches) void start(true);
    });
    card.addEventListener("pointerleave", (event) => {
      if (event.pointerType !== "touch") pause();
    });
    card.addEventListener("focusout", () => {
      window.setTimeout(() => {
        if (!card.contains(document.activeElement) && !card.matches(":hover")) pause();
      }, 0);
    });
    video.addEventListener("play", () => {
      if (!wantsPlayback) video.pause();
      sync();
    });
    video.addEventListener("pause", sync);
    video.addEventListener("volumechange", sync);
    video.addEventListener("error", () => {
      pause();
      status.textContent = "This film could not load. Open it directly or try again later.";
    });
    const syncCaptions = () => {
      for (const track of video.textTracks) track.mode = showCaptions ? "showing" : "disabled";
    };
    captions?.addEventListener("click", () => {
      showCaptions = !showCaptions;
      captions.setAttribute("aria-pressed", String(showCaptions));
      syncCaptions();
    });
    video.addEventListener("loadedmetadata", syncCaptions);
    card.querySelector("track")?.addEventListener("error", () => {
      status.textContent = "Captions could not load. Check the film description for a transcript.";
    });
    // Native controls remain the fallback if this enhancement never runs.
    controls.hidden = false;
    video.controls = false;
    players.push({ card, pause });
    sync();
  });
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting || entry.intersectionRatio < .15) {
          players.find(player => player.card === entry.target)?.pause();
        }
      });
    }, { threshold: [0, .15] });
    players.forEach(player => observer.observe(player.card));
  }
  const pauseAll = () => players.forEach(player => player.pause());
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) { pauseAll(); resetDepth(); }
  });
  window.addEventListener("pagehide", pauseAll);
  reducedMotion.addEventListener("change", () => {
    pausedMotion = reducedMotion.matches;
    pauseAll();
    syncMotion();
  });
  finePointer.addEventListener("change", () => { pauseAll(); syncMotion(); });
})();
