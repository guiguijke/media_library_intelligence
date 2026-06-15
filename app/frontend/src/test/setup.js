import '@testing-library/jest-dom'

beforeAll(() => {
  Object.defineProperty(window, 'location', {
    writable: true,
    value: { ...window.location, assign: vi.fn() },
  })
})

afterEach(() => {
  window.location.assign.mockClear?.()
})
