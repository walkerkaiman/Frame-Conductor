// Playwright test spec for Frame Conductor GUI
// Run with: npx playwright test

const { test, expect } = require('@playwright/test');

const APP_URL = 'http://localhost:5173';

test.describe('Frame Conductor GUI', () => {
  test('Config fields display and can be changed/saved', async ({ page }) => {
    await page.goto(APP_URL);
    const totalFramesInput = page.getByLabel('Total Frames:');
    const frameRateInput = page.getByLabel('Frame Rate (fps):');
    await expect(totalFramesInput).toHaveValue('1000');
    await expect(frameRateInput).toHaveValue('30');
    await totalFramesInput.fill('1234');
    await frameRateInput.fill('25');
    await page.getByRole('button', { name: /save config/i }).click();
    // Wait for status to reset
    await expect(page.getByText('Status:')).toContainText('Ready');
    // Reload and check values persisted
    await page.reload();
    await expect(totalFramesInput).toHaveValue('1234');
    await expect(frameRateInput).toHaveValue('25');
  });

  test('Start, Pause/Resume, and Reset buttons work', async ({ page }) => {
    await page.goto(APP_URL);
    const startBtn = page.getByRole('button', { name: /start|resume|pause/i });
    const resetBtn = page.getByRole('button', { name: /reset/i });
    // Start
    await startBtn.click();
    await expect(page.getByText('Status:')).toContainText('Sending frames');
    // Pause
    await startBtn.click();
    await expect(page.getByText('Status:')).toContainText('Paused');
    // Resume
    await startBtn.click();
    await expect(page.getByText('Status:')).toContainText('Sending frames');
    // Reset
    await resetBtn.click();
    await expect(page.getByText('Status:')).toContainText('Ready');
    await expect(page.getByText(/Current Frame:/)).toContainText('0');
  });

  test('Progress bar and label update as frames are sent', async ({ page }) => {
    await page.goto(APP_URL);
    const startBtn = page.getByRole('button', { name: /start/i });
    await startBtn.click();
    // Wait for progress to advance
    await page.waitForTimeout(1000);
    const progressLabel = page.getByText(/\d+ \/ \d+ \(\d+%\)/);
    await expect(progressLabel).not.toHaveText('0 / 1000 (0%)');
  });
}); 