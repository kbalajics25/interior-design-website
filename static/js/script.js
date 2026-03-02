document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.getElementById("navToggle");
  const mainNav = document.getElementById("mainNav");

  if (navToggle && mainNav) {
    navToggle.addEventListener("click", () => {
      mainNav.classList.toggle("open");
    });
  }

  const contactForm = document.getElementById("contactForm");
  if (!contactForm) return;

  const nameInput = document.getElementById("name");
  const mobileInput = document.getElementById("mobile_number");
  const nameError = document.getElementById("nameError");
  const mobileError = document.getElementById("mobileError");
  const formMessage = document.getElementById("formMessage");

  function resetMessages() {
    if (nameError) nameError.textContent = "";
    if (mobileError) mobileError.textContent = "";
    if (formMessage) {
      formMessage.textContent = "";
      formMessage.classList.remove("success", "error");
    }
  }

  function validateForm() {
    let valid = true;
    const name = nameInput.value.trim();
    const mobile = mobileInput.value.trim();

    resetMessages();

    if (!name) {
      nameError.textContent = "Name is required.";
      valid = false;
    }

    if (!mobile) {
      mobileError.textContent = "Mobile number is required.";
      valid = false;
    } else if (!/^\d{10}$/.test(mobile)) {
      mobileError.textContent = "Mobile number must be exactly 10 digits.";
      valid = false;
    }

    return valid;
  }

  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    const payload = {
      name: nameInput.value.trim(),
      mobile_number: mobileInput.value.trim(),
    };

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        formMessage.textContent =
          data.message || "Thank you! We will contact you soon.";
        formMessage.classList.add("success");
        nameInput.value = "";
        mobileInput.value = "";
      } else {
        if (data.errors) {
          if (data.errors.name && nameError) {
            nameError.textContent = data.errors.name;
          }
          if (data.errors.mobile_number && mobileError) {
            mobileError.textContent = data.errors.mobile_number;
          }
        }

        formMessage.textContent =
          data.message ||
          "There was a problem submitting the form. Please try again.";
        formMessage.classList.add("error");
      }
    } catch (error) {
      formMessage.textContent =
        "Network error. Please check your connection and try again.";
      formMessage.classList.add("error");
    }
  });
});

