import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import { useCurrentUser } from '../api/auth'
import type { FeedType } from '../types'

const empty = { name: '', maxAmountKg: 1 }

export default function FeedTypes() {
  const me = useCurrentUser()
  const isAdmin = me?.role === 'admin'
  const isStaff = me?.role === 'admin' || me?.role === 'technician'

  const [rows, setRows] = useState<FeedType[]>([])
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')

  async function load() {
    const data = await api<FeedType[]>('/api/feed-types')
    setRows(data)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/feed-types', {
        method: 'POST',
        body: JSON.stringify({ ...form, isActive: true }),
      })
      setForm(empty)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  async function patch(id: number, body: Partial<FeedType>) {
    setError('')
    try {
      await api(`/api/feed-types/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失败')
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>饵料类型白名单</h1>
        <p className="muted">
          全场通用。类型名去空白后唯一；停用仅场长可操作，停用后新投喂与改类型均不可再用。
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      {isStaff && (
        <form className="panel form-grid" onSubmit={onSubmit}>
          <label>
            类型名
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </label>
          <label>
            最大单次 kg
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={form.maxAmountKg}
              onChange={(e) =>
                setForm({ ...form, maxAmountKg: Number(e.target.value) })
              }
              required
            />
          </label>
          <button type="submit" className="btn primary">
            新增启用类型
          </button>
        </form>
      )}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>类型名</th>
              <th>状态</th>
              <th>最大单次 kg</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.isActive ? '' : 'row-disabled'}>
                <td>{r.id}</td>
                <td>
                  <InlineName row={r} editable={isStaff} onSave={(name) => patch(r.id, { name })} />
                </td>
                <td>{r.isActive ? '启用' : '已停用'}</td>
                <td>
                  <InlineMax
                    row={r}
                    editable={isStaff}
                    onSave={(maxAmountKg) => patch(r.id, { maxAmountKg })}
                  />
                </td>
                <td>
                  {r.isActive ? (
                    <button
                      className="btn ghost danger"
                      disabled={!isAdmin}
                      title={isAdmin ? undefined : '停用类型仅场长可操作'}
                      onClick={() =>
                        confirm(`确认停用「${r.name}」?停用后新投喂不可再用。`) &&
                        patch(r.id, { isActive: false })
                      }
                    >
                      停用
                    </button>
                  ) : isStaff ? (
                    <button className="btn ghost" onClick={() => patch(r.id, { isActive: true })}>
                      重新启用
                    </button>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function InlineName({
  row,
  editable,
  onSave,
}: {
  row: FeedType
  editable: boolean
  onSave: (name: string) => void
}) {
  const [v, setV] = useState(row.name)
  const [editing, setEditing] = useState(false)
  if (!editing) {
    return (
      <span>
        {row.name}
        {editable && (
          <button className="btn link" onClick={() => setEditing(true)}>
            改名
          </button>
        )}
      </span>
    )
  }
  return (
    <span className="inline-edit">
      <input value={v} onChange={(e) => setV(e.target.value)} />
      <button
        className="btn tiny"
        onClick={() => {
          if (v.trim()) {
            onSave(v.trim())
            setEditing(false)
          }
        }}
      >
        保存
      </button>
      <button
        className="btn tiny ghost"
        onClick={() => {
          setV(row.name)
          setEditing(false)
        }}
      >
        取消
      </button>
    </span>
  )
}

function InlineMax({
  row,
  editable,
  onSave,
}: {
  row: FeedType
  editable: boolean
  onSave: (maxAmountKg: number) => void
}) {
  const [v, setV] = useState(String(row.maxAmountKg))
  const [editing, setEditing] = useState(false)
  if (!editing) {
    return (
      <span>
        {row.maxAmountKg}
        {editable && (
          <button className="btn link" onClick={() => setEditing(true)}>
            调整
          </button>
        )}
      </span>
    )
  }
  return (
    <span className="inline-edit">
      <input
        type="number"
        step="0.01"
        min="0.01"
        value={v}
        onChange={(e) => setV(e.target.value)}
      />
      <button
        className="btn tiny"
        onClick={() => {
          const n = Number(v)
          if (n > 0) {
            onSave(n)
            setEditing(false)
          }
        }}
      >
        保存
      </button>
      <button
        className="btn tiny ghost"
        onClick={() => {
          setV(String(row.maxAmountKg))
          setEditing(false)
        }}
      >
        取消
      </button>
    </span>
  )
}
