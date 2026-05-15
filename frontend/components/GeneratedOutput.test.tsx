
import { afterEach, assert, beforeEach, test, vi } from 'vitest'
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import GeneratedOutput from './GeneratedOutput'

const SHORT_OUTPUT = 'Weekend trip to Portland with coffee stops and museum visits.'
const LONG_OUTPUT = Array.from({ length: 40 }, (_, index) => `Day ${index + 1}: Explore stop ${index + 1}.`).join('\n')

const originalClipboard = navigator.clipboard

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.runOnlyPendingTimers()
  vi.useRealTimers()
  vi.restoreAllMocks()

  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: originalClipboard,
  })
})

test('copies the full short generated output and resets the success state after timeout', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText },
  })

  render(<GeneratedOutput output={SHORT_OUTPUT} />)

  fireEvent.click(screen.getByRole('button', { name: /copy/i }))

  await waitFor(() => {
    assert.equal(writeText.mock.calls[0][0], SHORT_OUTPUT)
  })

  assert.ok(screen.getByRole('button', { name: /copied/i }))

  await act(async () => {
    vi.advanceTimersByTime(2000)
  })

  assert.ok(screen.getByRole('button', { name: /copy/i }))
})

test('copies the full long generated output without truncation', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined)

  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText },
  })

  render(<GeneratedOutput output={LONG_OUTPUT} />)

  fireEvent.click(screen.getByRole('button', { name: /copy/i }))

  await waitFor(() => {
    assert.equal(writeText.mock.calls[0][0], LONG_OUTPUT)
  })

  assert.ok(screen.getByRole('button', { name: /copied/i }))
})

test('renders an error message when the clipboard API rejects', async () => {
  const writeText = vi.fn().mockRejectedValue(new Error('Clipboard unavailable'))

  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText },
  })

  render(<GeneratedOutput output={SHORT_OUTPUT} />)

  fireEvent.click(screen.getByRole('button', { name: /copy/i }))

  await waitFor(() => {
    assert.ok(screen.getByText(/unable to copy/i))
  })

  assert.ok(screen.getByRole('button', { name: /copy/i }))
})
