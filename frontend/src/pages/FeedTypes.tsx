import { FormEvent, useEffect, useState } from 'react'
import { api, getStoredUser } from '../api/client'
import type { FeedType } from '../types'

const empty = { name: '', maxAmountKg: 1 }

export default function FeedTypes() {
  const [rows, setRows] = useState<FeedType[]>([])
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editMax, setEditMax] = useState('')
  const role = getStoredUser()?.role ?? ''
  const isAdmin = role === 'admin'

  async function load() {
    const list = await api<FeedType[]>('/api/feed-types')
    setRows(list)
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setInfo('')
    try {
      await api('/api/feed-types', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setForm(empty)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  async function startEdit(t: FeedType) {
    setEditingId(t.id)
    setEditMax(String(t.maxAmountKg))
    setError('')
  }

  async function saveMax(t: FeedType) {
    const maxAmountKg = Number(editMax)
    if (!(maxAmountKg > 0)) {
      setError('最大单次千克必须为正数')
      return
    }
    setError('')
    try {
      await api(`/api/feed-types/${t.id}`, {
        method: 'PUT',
        body: JSON.stringify({ maxAmountKg }),
      })
      setEditingId(null)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失败')
    }
  }

  async function deactivate(t: FeedType) {
    if (!confirm(`确认停用饵料类型「${t.name}」？停用后新投喂与改类型均不可再用。`)) return
    setError('')
    try {
      await api(`/api/feed-types/${t.id}`, {
        method: 'PUT',
        body: JSON.stringify({ isActive: false }),
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '停用失败')
    }
  }

  async function reactivate(t: FeedType) {
    setError('')
    try {
      await api(`/api/feed-types/${t.id}`, {
        method: 'PUT',
        body: JSON.stringify({ isActive: true }),
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '启用失败')
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>饵料类型白名单</h1>
        <p className="muted">
          投喂仅可使用启用类型且不超过最大单次千克。技术员可增改；停用仅场长。
        </p>
      </header>
      {error && <div className="error">{error}</div>}
      {info && <div className="muted">{info}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          类型名
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="如 轮虫"
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
            onChange={(e) => setForm({ ...form, maxAmountKg: Number(e.target.value) })}
            required
          />
        </label>
        <button type="submit" className="btn primary">
          新增类型
        </button>
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>类型名</th>
              <th>状态</th>
              <th>最大单次 kg</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id} style={t.isActive ? undefined : { opacity: 0.55 }}>
                <td>{t.id}</td>
                <td>{t.name}</td>
                <td>{t.isActive ? '启用' : '已停用'}</td>
                <td>
                  {editingId === t.id ? (
                    <input
                      type="number"
                      step="0.01"
                      min="0.01"
                      value={editMax}
                      onChange={(e) => setEditMax(e.target.value)}
                    />
                  ) : (
                    t.maxAmountKg
                  )}
                </td>
                <td>
                  {editingId === t.id ? (
                    <>
                      <button className="btn primary" onClick={() => saveMax(t)}>
                        保存
                      </button>{' '}
                      <button className="btn ghost" onClick={() => setEditingId(null)}>
                        取消
                      </button>
                    </>
                  ) : (
                    <>
                      <button className="btn ghost" onClick={() => startEdit(t)}>
                        改上限
                      </button>{' '}
                      {t.isActive
                        ? isAdmin && (
                            <button className="btn ghost" onClick={() => deactivate(t)}>
                              停用
                            </button>
                          )
                        : isAdmin && (
                            <button className="btn ghost" onClick={() => reactivate(t)}>
                              重新启用
                            </button>
                          )}
                      {!isAdmin && t.isActive && (
                        <span className="muted">停用需场长</span>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
