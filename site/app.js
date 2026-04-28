(function () {
  const config = window.APP_CONFIG || {};
  const repoUrl = config.repoUrl || "https://github.com/cloudsecmentor/geotagcopy";
  const releasesUrl = `${repoUrl}/releases/latest`;

  function byId(id) {
    return document.getElementById(id);
  }

  function setRepoLinks() {
    document.querySelectorAll("[data-repo-link]").forEach((link) => {
      link.href = repoUrl;
    });
  }

  function configureDonateLink() {
    const donateLink = byId("donate-link");
    const donateNote = byId("donate-note");
    const paymentLink = (config.stripePaymentLink || "").trim();

    if (!donateLink) {
      return;
    }

    if (paymentLink && !paymentLink.startsWith("__")) {
      donateLink.href = paymentLink;
      donateLink.removeAttribute("aria-disabled");
      if (donateNote) {
        donateNote.textContent = "Payment is handled by Stripe in your browser.";
      }
      return;
    }

    donateLink.addEventListener("click", (event) => event.preventDefault());
  }

  function setDownloadFallback(message) {
    const latestVersion = byId("latest-version");
    const targets = [
      byId("download-macos"),
      byId("download-windows")
    ];

    if (latestVersion) {
      latestVersion.textContent = message || "Latest downloads are available on GitHub.";
    }

    targets.forEach((target) => {
      if (target) {
        target.href = releasesUrl;
      }
    });
  }

  function applyLatestRelease(data) {
    const version = data.version || "latest";
    const latestVersion = byId("latest-version");
    const downloads = {
      "download-macos": data.macos && data.macos.app,
      "download-windows": data.windows && data.windows.app
    };

    if (latestVersion) {
      latestVersion.textContent = `Latest version: ${version}`;
    }

    Object.entries(downloads).forEach(([id, url]) => {
      const link = byId(id);
      if (!link) {
        return;
      }
      link.href = url || releasesUrl;
    });
  }

  function loadLatestRelease() {
    const latestJsonUrl = config.latestJsonUrl || "latest.json";

    fetch(latestJsonUrl, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`latest.json returned ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        const hasDownloads =
          data &&
          data.macos &&
          data.windows &&
          (data.macos.app || data.windows.app);

        if (!hasDownloads) {
          setDownloadFallback("Release downloads are coming soon.");
          return;
        }

        applyLatestRelease(data);
      })
      .catch(() => {
        setDownloadFallback("Latest downloads are available on GitHub.");
      });
  }

  setRepoLinks();
  configureDonateLink();
  setDownloadFallback("Checking latest version...");
  loadLatestRelease();
})();
