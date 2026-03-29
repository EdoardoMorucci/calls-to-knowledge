import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../StatusBadge'

describe('StatusBadge', () => {
  it.each([
    ['done', 'DONE'],
    ['recording', 'REC'],
    ['processing', 'PROCESSING'],
    ['error', 'ERROR'],
  ])('mostra label corretta per stato %s', (status, label) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('usa fallback ERROR per stato sconosciuto', () => {
    render(<StatusBadge status="unknown" />)
    expect(screen.getByText('ERROR')).toBeInTheDocument()
  })
})
