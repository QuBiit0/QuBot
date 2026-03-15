import { chromium } from 'playwright';

async function setup() {
    console.log('Installing Playwright browsers...');
    try {
        const browser = await chromium.launch();
        console.log('Chromium launched successfully.');
        await browser.close();
        console.log('Setup complete.');
    } catch (error) {
        console.error('Error launching Chromium:', error);
        process.exit(1);
    }
}

setup();
