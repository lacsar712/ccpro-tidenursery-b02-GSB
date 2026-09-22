import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { FeedEvent, FeedType, Pond } from '../types'

function nowLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

type FormState = {
  pondId: number
  fedAt: string
  feedType: string
  amountKg: number | ''
  operatorName: string
  mixRatioPct: string
}

const emptyForm = (feedType = '', pondId = 0): FormState => ({
  pondId,
  fedAt: nowLocal(),
  feedType,
  amountKg: '',
  operatorName: '水质技术员',
  mixRatioPct: '',
})

export default function FeedEvents() {
  const [ponds, setPonds] = useState<Pond[]>([])
  // 下拉只取启用类型,停用类型不会出现
  const [feedTypes, setFeedTypes] = useState<FeedType[]>([])
  const [rows, setRows] = useState<FeedEvent[]>([])
  const [form, setForm] = useState<FormState>(emptyForm())
  const [editingId, setEditingId] = useState<number | null>(null)
  const [error, setError] = useState('')

  async function load() {
    const [ps, fts, es] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<FeedType[]>('/api/feed-types?active=true'),
      api<FeedEvent[]>('/api/feed-events'),
    ])
    setPonds(ps)
    setFeedTypes(fts)
    setRows(es)
    setForm((f) =>
      f.pondId ? f : { ...f, pondId: ps[0]?.id ?? 0, feedType: f.feedType || fts[0]?.name || '' },
    )
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  const selectedType = feedTypes.find((t) => t.name === form.feedType)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    const amount = Number(form.amountKg)
    if (!(amount > 0)) {
      setError('投喂量必须为正数')
      return
    }
    if (form.mixRatioPct !== '') {
      const r = Number(form.mixRatioPct)
      if (!Number.isInteger(r) || r < 1 || r > 100) {
        setError('混喂比例须为 1–100 的整数,或留空')
        return
      }
    }
    const body = {
      pondId: form.pondId,
      fedAt: new Date(form.fedAt).toISOString(),
      feedType: form.feedType,
      amountKg: amount,
      operatorName: form.operatorName,
      mixRatioPct: form.mixRatioPct === '' ? null : Number(form.mixRatioPct),
    }
    try {
      if (editingId === null) {
        await api('/api/feed-events', { method: 'POST', body: JSON.stringify(body) })
        resetForm()
      } else {
        await api(`/api/feed-events/${editingId}`, { method: 'PUT', body: JSON.stringify(body) })
        resetForm()
      }
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
  }

  function resetForm() {
    setEditingId(null)
    setForm((f) => emptyForm(feedTypes[0]?.name || '', f.pondId))
  }

  function startEdit(r: FeedEvent) {
    setEditingId(r.id)
    setError('')
    const d = new Date(r.fedAt)
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
    setForm({
      pondId: r.pondId,
      fedAt: d.toISOString().slice(0, 16),
      // 停用类型的旧记录:下拉里没有该项,额外补一个临时选项,
      // 但用户一旦改选其他类型就无法再选回(接口同样拒绝停用类型)
      feedType: r.feedType,
      amountKg: r.amountKg,
      operatorName: r.operatorName,
      mixRatioPct: r.mixRatioPct == null ? '' : String(r.mixRatioPct),
    })
  }

  async function remove(id: number) {
    if (!confirm('确认删除该投喂记录?')) return
    try {
      await api(`/api/feed-events/${id}`, { method: 'DELETE' })
      if (editingId === id) resetForm()
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '删除失败')
    }
  }

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} (${p.species})` : `#${id}`
  }

  // 下拉选项:启用类型 + 编辑旧记录时临时带入的停用类型
  const optionNames = new Set(feedTypes.map((t) => t.name))
  if (editingId !== null && form.feedType && !optionNames.has(form.feedType)) {
    optionNames.add(form.feedType)
  }
  const typeActive = (name: string) => feedTypes.some((t) => t.name === name)

  return (
    <div>
      <header className="page-header">
        <h1>投喂事件</h1>
        <p className="muted">
          饵料类型须命中启用白名单,且不超过该类型最大单次千克;停用类型旧记录可读但不可再选。
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        {editingId !== null && (
          <div className="form-banner span-2">正在编辑投喂记录 #{editingId}</div>
        )}
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
          饵料类型
          <select
            value={form.feedType}
            onChange={(e) => setForm({ ...form, feedType: e.target.value })}
            required
          >
            {[...optionNames].map((name) => (
              <option key={name} value={name}>
                {name}
                {typeActive(name) ? '' : '(已停用)'}
              </option>
            ))}
          </select>
          {selectedType && (
            <small className="muted">该类型单次最大 {selectedType.maxAmountKg} kg</small>
          )}
        </label>
        <label>
          投喂量 kg
          <input
            type="number"
            step="0.01"
            min="0.01"
            max={selectedType?.maxAmountKg}
            value={form.amountKg}
            onChange={(e) => setForm({ ...form, amountKg: e.target.value === '' ? '' : Number(e.target.value) })}
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
          混喂比例 % (可选,1–100)
          <input
            type="number"
            step="1"
            min="1"
            max="100"
            value={form.mixRatioPct}
            onChange={(e) => setForm({ ...form, mixRatioPct: e.target.value })}
          />
        </label>
        <div className="form-actions">
          <button type="submit" className="btn primary">
            {editingId === null ? '登记投喂' : '保存修改'}
          </button>
          {editingId !== null && (
            <button type="button" className="btn ghost" onClick={resetForm}>
              取消编辑
            </button>
          )}
        </div>
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
              <tr key={r.id} className={typeActive(r.feedType) ? '' : 'row-disabled'}>
                <td>{r.id}</td>
                <td>{pondLabel(r.pondId)}</td>
                <td>{new Date(r.fedAt).toLocaleString()}</td>
                <td>
                  {r.feedType}
                  {!typeActive(r.feedType) && <span className="tag-muted">已停用</span>}
                </td>
                <td>{r.amountKg}</td>
                <td>{r.mixRatioPct == null ? '—' : r.mixRatioPct}</td>
                <td>{r.operatorName}</td>
                <td className="row-actions">
                  <button className="btn ghost" onClick={() => startEdit(r)}>
                    编辑
                  </button>
                  <button className="btn ghost danger" onClick={() => remove(r.id)}>
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
