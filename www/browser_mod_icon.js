// browser_mod_icon.js
// hide browser_mod "require interaction" icon, doesn't add value to me

const style = document.createElement('style');

style.textContent = `
  .browser-mod-require-interaction {
    display: none;
  }
`;

document.head.appendChild(style);