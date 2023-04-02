// different custom scripts to fix small UI issues


// rename the gas consumption header in the energy dashboard
const energyPanel = document.querySelector('body>home-assistant')?.shadowRoot.querySelector('home-assistant-main')?.shadowRoot.querySelector('app-drawer-layout>partial-panel-resolver>ha-panel-energy')?.shadowRoot.querySelector('ha-app-layout>hui-view>hui-sidebar-view');
const gasTitle = energyPanel?.shadowRoot.querySelector('#main>hui-energy-gas-graph-card')?.shadowRoot.querySelector('ha-card>h1');

if (gasTitle) {
  gasTitle.textContent = "Energy by device";
}

const gasGraphTitle = energyPanel?.shadowRoot.querySelector('#sidebar>hui-energy-distribution-card')?.shadowRoot.querySelector('ha-card>div>div:nth-child(1)>div.circle-container.gas>span');

if (gasGraphTitle) {
  gasGraphTitle.textContent = "Devices";
}