import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { FeedEvent, FeedType, Pond } from '../types'

function nowLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const empty = {
  pondId: 0,
  fedAt: nowLocal(),
  feedType: '',
  amountKg: 1,
  operatorName: '水质技术员',
  mixRatioPct: '' as '' | number,
}

export default function FeedEvents() {
  const [ponds, setPonds] = useState<Pond[]>([])
  const [types, setTypes] = useState<FeedType[]>([])
  const [rows, setRows] = useState<FeedEvent[]>([])
  const [form, setForm] = useState(empty)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState<number | null>(null)

  async function load() {
    const [ps, ts, es] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<FeedType[]>('/api/feed-types?active=true'),
      api<FeedEvent[]>('/api/feed-events'),
    ])
    setPonds(ps)
    setTypes(ts)
    setRows(es)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
    // 默认选中第一个启用类型（仅新建时）
    if (!form.feedType && ts[0]) {
      setForm((f) => ({ ...f, feedType: ts[0].name, amountKg: 1 }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const selectedType = types.find((t) => t.name === form.feedType)
  const maxKg = selectedType?.maxAmountKg

  function chooseFeedType(name: string) {
    const t = types.find((x) => x.name === name)
    setForm((f) => ({
      ...f,
      feedType: name,
      // 超过该项最大单次千克时，回收到上限以内
      amountKg: t ? Math.min(f.amountKg || 0, t.maxAmountKg) || t.maxAmountKg : f.amountKg,
    }))
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (mixInvalid) return
    const body: Record<string, unknown> = {
      pondId: form.pondId,
      fedAt: new Date(form.fedAt).toISOString(),
      feedType: form.feedType,
      amountKg: form.amountKg,
      operatorName: form.operatorName,
    }
    if (form.mixRatioPct !== '') body.mixRatioPct = form.mixRatioPct
    try {
      if (editingId === null) {
        await api('/api/feed-events', { method: 'POST', body: JSON.stringify(body) })
      } else {
        await api(`/api/feed-events/${editingId}`, {
          method: 'PUT',
          body: JSON.stringify(body),
        })
      }
      setForm((f) => ({
        ...empty,
        pondId: f.pondId,
        feedType: types[0]?.name ?? '',
        amountKg: types[0] ? Math.min(1, types[0].maxAmountKg) : 1,
        fedAt: nowLocal(),
      }))
      setEditingId(null)
      await load()
    } catch (err) {
      // 409 正文已列出当前启用类型，直接展示
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  const mixValue = form.mixRatioPct
  const mixInvalid =
    mixValue !== '' && (!Number.isInteger(Number(mixValue)) || Number(mixValue) < 1 || Number(mixValue) > 100)

  function startEdit(r: FeedEvent) {
    setError('')
    setEditingId(r.id)
    // 停用类型的旧记录：下拉不含它，明确提示不可再选该类型
    if (!types.some((t) => t.name === r.feedType)) {
      setError(`该记录使用的「${r.feedType}」已停用，请改选一个启用类型后再保存。`)
    }
    const d = new Date(r.fedAt)
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
    setForm({
      pondId: r.pondId,
      fedAt: d.toISOString().slice(0, 16),
      feedType: types.some((t) => t.name === r.feedType) ? r.feedType : types[0]?.name ?? '',
      amountKg: r.amountKg,
      operatorName: r.operatorName,
      mixRatioPct: r.mixRatioPct ?? '',
    })
  }

  function cancelEdit() {
    setEditingId(null)
    setError('')
    setForm((f) => ({
      ...empty,
      pondId: f.pondId,
      feedType: types[0]?.name ?? '',
      fedAt: nowLocal(),
    }))
  }

  async function remove(id: number) {
    if (!confirm('确认删除该投喂记录？')) return
    try {
      await api(`/api/feed-events/${id}`, { method: 'DELETE' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} (${p.species})` : `#${id}`
  }

  const typeActive = (name: string) => types.some((t) => t.name === name)

  return (
    <div>
      <header className="page-header">
        <h1>投喂事件</h1>
        <p className="muted">饵料类型须命中启用白名单，且不超过该项最大单次千克</p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          塘口
          <select
            value={form.pondId}
            onChange={(e) => setForm({ ...form, pondId: Number(e.target.value) })}
            required
          >
            {ponds.map((p) => (
              <option key={p.id} value={p.id}>
                {p.pondCode} · {p.species}
              </option>
            ))}
          </select>
        </label>
        <label>
          投喂时间
          <input
            type="datetime-local"
            value={form.fedAt}
            onChange={(e) => setForm({ ...form, fedAt: e.target.value })}
            required
          />
        </label>
        <label>
          饵料类型（仅启用）
          <select
            value={form.feedType}
            onChange={(e) => chooseFeedType(e.target.value)}
            required
          >
            {types.map((t) => (
              <option key={t.id} value={t.name}>
                {t.name}（≤{t.maxAmountKg}kg）
              </option>
            ))}
          </select>
        </label>
        <label>
          投喂量 kg{maxKg ? `（上限 ${maxKg}kg）` : ''}
          <input
            type="number"
            step="0.01"
            min="0.01"
            max={maxKg}
            value={form.amountKg}
            onChange={(e) => setForm({ ...form, amountKg: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          操作人
          <input
            value={form.operatorName}
            onChange={(e) => setForm({ ...form, operatorName: e.target.value })}
            required
          />
        </label>
        <label>
          混喂比例 %（选填 1-100）
          <input
            type="number"
            step="1"
            min="1"
            max="100"
            value={form.mixRatioPct}
            onChange={(e) =>
              setForm({
                ...form,
                mixRatioPct: e.target.value === '' ? '' : Number(e.target.value),
              })
            }
          />
        </label>
        {mixInvalid && (
          <div className="error">混喂比例须为 1 到 100 的整数</div>
        )}
        <button type="submit" className="btn primary">
          {editingId === null ? '登记投喂' : '保存修改'}
        </button>
        {editingId !== null && (
          <button type="button" className="btn ghost" onClick={cancelEdit}>
            取消编辑
          </button>
        )}
      </form>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>塘口</th>
              <th>投喂时间</th>
              <th>饵料</th>
              <th>数量 kg</th>
              <th>混喂 %</th>
              <th>操作人</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{pondLabel(r.pondId)}</td>
                <td>{new Date(r.fedAt).toLocaleString()}</td>
                <td>
                  {r.feedType}
                  {!typeActive(r.feedType) && (
                    <span className="muted">（已停用·旧记录）</span>
                  )}
                </td>
                <td>{r.amountKg}</td>
                <td>{r.mixRatioPct ?? '—'}</td>
                <td>{r.operatorName}</td>
                <td>
                  <button className="btn ghost" onClick={() => startEdit(r)}>
                    编辑
                  </button>{' '}
                  <button className="btn ghost" onClick={() => remove(r.id)}>
                    删除
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
