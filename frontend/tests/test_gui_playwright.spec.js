import { test, expect } from '@playwright/test';

const APP_URL = 'http://localhost:5173';
const API_URL = 'http://localhost:9000/api';

// Helper to wait for backend to process
async function waitForStatus(page, expected, timeout = 3000) {
  await expect(page.locator('text=Status:')).toHaveText(new RegExp(expected), { timeout });
}

// Helper to poll for summary update
async function waitForSummary(page, expected, timeout = 5000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const summary = await page.locator('div:has-text("Total Frames:")').last().innerText();
    if (summary.includes(expected)) return;
    await page.waitForTimeout(100);
  }
  throw new Error(`Timed out waiting for summary to contain: ${expected}`);
}

test.describe('Frame Conductor End-to-End', () => {
  test('Full user flow: config, play, pause, resume, reset', async ({ page }) => {
    // 1. Load the app
    await page.goto(APP_URL);
    await expect(page.locator('text=Frame Conductor')).toBeVisible();
    await expect(page.getByLabel('Total Frames:')).toBeVisible();
    await expect(page.getByLabel('Frame Rate (fps):')).toBeVisible();
    await expect(page.locator('text=Status:')).toBeVisible();
    await expect(page.locator('text=Controls')).toBeVisible();
    await expect(page.locator('text=Progress')).toBeVisible();

    // 2. Change Total Frames and Frame Rate (simulate real user input)
    const totalFramesInput = page.getByLabel('Total Frames:');
    const frameRateInput = page.getByLabel('Frame Rate (fps):');
    await totalFramesInput.click();
    await totalFramesInput.press('Control+A');
    await totalFramesInput.type('12');
    await frameRateInput.click();
    await frameRateInput.press('Control+A');
    await frameRateInput.type('5');
    await page.waitForTimeout(100);
    const debugInput = await totalFramesInput.inputValue();
    console.log('DEBUG: Input value after type:', debugInput);
    await expect(totalFramesInput).toHaveValue('12');
    await expect(frameRateInput).toHaveValue('5');

    // 3. Save Config
    await page.click('button:has-text("Save Config")');
    await waitForStatus(page, 'Ready');
    // Debug print the summary value after save
    const debugSummary = await page.locator('div:has-text("Total Frames:")').last().innerText();
    console.log('DEBUG: Summary after save:', debugSummary);
    // Wait for the summary to update to the new value
    await waitForSummary(page, '12', 5000);

    // 4. Start sending frames
    await page.click('button:has-text("Start")');
    await waitForStatus(page, 'Sending frames');
    // Wait for progress to increment (use .last() to avoid strict mode violation)
    const currentFrameSummary = page.locator('div:has-text("Current Frame:")').last();
    await expect(currentFrameSummary).not.toContainText('0');

    // 5. Pause
    await page.click('button:has-text("Pause")');
    await waitForStatus(page, 'Paused');
    // Confirm frame does not increment for a short period
    const framePaused = await currentFrameSummary.innerText();
    await page.waitForTimeout(1000);
    const framePaused2 = await currentFrameSummary.innerText();
    expect(framePaused2).toBe(framePaused);

    // 6. Resume
    await page.click('button:has-text("Resume")');
    await waitForStatus(page, 'Sending frames');
    // Confirm frame increments again
    await page.waitForTimeout(1000);
    const frameAfterResume = await currentFrameSummary.innerText();
    expect(Number(frameAfterResume.match(/\d+/)[0])).toBeGreaterThan(Number(framePaused.match(/\d+/)[0]));

    // 7. Reset
    await page.click('button:has-text("Reset")');
    await waitForStatus(page, 'Ready');
    await expect(currentFrameSummary).toContainText('0');

    // 8. Confirm backend/frontend communication by changing config again
    await totalFramesInput.click();
    await totalFramesInput.press('Control+A');
    await totalFramesInput.type('15');
    await frameRateInput.click();
    await frameRateInput.press('Control+A');
    await frameRateInput.type('10');
    await page.click('button:has-text("Save Config")');
    await waitForStatus(page, 'Ready');
    await waitForSummary(page, '15', 5000);
  });
}); 