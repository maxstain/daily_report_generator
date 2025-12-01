import pytest

# This test uses pytest-playwright fixtures. Install playwright and run `playwright install` first.

@pytest.mark.asyncio
async def test_dynamic_ui_and_preview(page):
    # start server locally before running this test (app must be running at http://127.0.0.1:5000)
    await page.goto('http://127.0.0.1:5000/')
    # Add a booking row
    await page.click('#add-booking-btn')
    # fill the first booking row inputs
    rem = await page.query_selector_all('.bk-remote')
    loc = await page.query_selector_all('.bk-location')
    start = await page.query_selector_all('.bk-start')
    end = await page.query_selector_all('.bk-end')
    await rem[0].fill('remote A')
    await start[0].fill('08:30')
    await end[0].fill('12:30')

    # Add a TE
    await page.click('#add-te-btn')
    ids = await page.query_selector_all('.te-id')
    summaries = await page.query_selector_all('.te-summary')
    tests = await page.query_selector_all('.te-tests')
    await ids[0].fill('SECONPRO-999')
    await summaries[0].fill('Sample Exec')
    await tests[0].fill('SECONPRO-1000')

    # Check live preview includes our entries
    preview = await page.inner_text('#livePreview')
    assert 'remote A' in preview
    assert 'SECONPRO-999' in preview

    # Trigger form submit (will navigate if server responds)
    # Instead of submitting, we'll check hidden fields serialization by calling the form submit handler via JS
    await page.evaluate('document.getElementById("reportForm").dispatchEvent(new Event("submit", {cancelable:true, bubbles:true}));')
    # Read hidden fields
    bookings_json = await page.input_value('#bookings_json')
    executions_json = await page.input_value('#executions_json')
    assert 'remote A' in bookings_json
    assert 'SECONPRO-999' in executions_json

