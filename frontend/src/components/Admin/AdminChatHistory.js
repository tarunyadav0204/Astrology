import React, { useState, useEffect, useMemo } from 'react';
import { getAdminAuthHeaders } from '../../services/adminService';
import { formatChatMessageHtml as formatMessageContent } from '../../utils/markdown';
import './AdminChatHistory.css';

const AdminChatHistory = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionQuery, setSessionQuery] = useState('');

  useEffect(() => {
    fetchAllChatHistory();
  }, []);

  const fetchAllChatHistory = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/chat/all-history', {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Error fetching all chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    try {
      const response = await fetch(`/api/admin/chat/session/${sessionId}`, {
        headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedSession(data);
      }
    } catch (error) {
      console.error('Error fetching session details:', error);
    }
  };

  const IST = 'Asia/Kolkata';

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const formatTimeIST = (dateStr) => {
    return new Date(dateStr).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZone: IST
    }) + ' IST';
  };

  const formatParallelStageLabel = (stage) => {
    const s = String(stage || '');
    return s.replace(/^parallel_/, '').replace(/_/g, ' ') || 'stage';
  };

  const formatParallelElapsed = (ms) => {
    if (ms == null || !Number.isFinite(Number(ms))) return null;
    const n = Number(ms);
    if (n >= 1000) return `${(n / 1000).toFixed(2)}s`;
    return `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })}ms`;
  };

  /** Sum a numeric field across parallel stage rows (orchestrator stores one row per branch + merge). */
  const sumParallelStageField = (stages, key) => {
    if (!Array.isArray(stages)) return 0;
    return stages.reduce((acc, st) => acc + (Number(st?.[key]) || 0), 0);
  };

  const formatLlmLabel = (s) => {
    const prov = (s.chat_llm_provider || '').trim();
    const mod = (s.chat_llm_model || '').trim();
    if (!mod && !prov) return null;
    if (prov && mod) return `${prov}: ${mod}`;
    return mod || prov || null;
  };

  const filteredSessions = useMemo(() => {
    const q = sessionQuery.trim().toLowerCase();
    if (!q) return sessions;
    return sessions.filter((s) => {
      const hay = [
        s.user_name,
        s.user_phone,
        s.native_name,
        s.preview,
        s.session_id,
        s.chat_llm_provider,
        s.chat_llm_model,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return hay.includes(q);
    });
  }, [sessions, sessionQuery]);

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape' && selectedSession) setSelectedSession(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selectedSession]);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 900px), (max-height: 700px)');
    const lock = () => {
      if (selectedSession && mq.matches) {
        document.body.classList.add('admin-chat-mobile-thread-active');
      } else {
        document.body.classList.remove('admin-chat-mobile-thread-active');
      }
    };
    lock();
    if (typeof mq.addEventListener === 'function') {
      mq.addEventListener('change', lock);
      return () => {
        mq.removeEventListener('change', lock);
        document.body.classList.remove('admin-chat-mobile-thread-active');
      };
    }
    mq.addListener(lock);
    return () => {
      mq.removeListener(lock);
      document.body.classList.remove('admin-chat-mobile-thread-active');
    };
  }, [selectedSession]);

  const msgCount = selectedSession?.messages?.length ?? 0;

  return (
    <div
      className={`admin-chat-history${
        selectedSession ? ' admin-chat-history--thread-open' : ''
      }`}
    >
      <div className="admin-chat-history-intro">
        <h2>Chat history</h2>
        <p className="admin-chat-history-hint admin-chat-history-hint--desktop">
          Open a session for a full-width transcript. Press <kbd>Esc</kbd> to close the
          conversation.
        </p>
        <p className="admin-chat-history-hint admin-chat-history-hint--mobile">
          Tap a session to open it full screen. Use <strong>Back</strong> or the close control to
          return here.
        </p>
      </div>

      <div className={`admin-chat-content ${selectedSession ? 'has-selection' : ''}`}>
        <aside className="sessions-sidebar" aria-label="Chat sessions">
          <div className="sessions-list-header">
            <h3>Sessions</h3>
            {!loading && sessions.length > 0 && (
              <span className="sessions-count">{sessions.length}</span>
            )}
          </div>
          {sessions.length > 0 && (
            <div className="sessions-search-wrap">
              <label className="sessions-search-label" htmlFor="admin-chat-session-filter">
                Filter
              </label>
              <input
                id="admin-chat-session-filter"
                type="search"
                className="sessions-search-input"
                placeholder="Name, phone, chart, model, preview…"
                value={sessionQuery}
                onChange={(e) => setSessionQuery(e.target.value)}
                autoComplete="off"
              />
            </div>
          )}
          <div className="sessions-list">
            {loading ? (
              <div className="loading">Loading sessions…</div>
            ) : sessions.length === 0 ? (
              <div className="no-sessions">No chat sessions found.</div>
            ) : filteredSessions.length === 0 ? (
              <div className="no-sessions">No sessions match your filter.</div>
            ) : (
              filteredSessions.map((session) => (
                <div
                  key={session.session_id}
                  role="button"
                  tabIndex={0}
                  className={`session-card ${
                    selectedSession?.session_id === session.session_id ? 'active' : ''
                  }`}
                  onClick={() => fetchSessionDetails(session.session_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      fetchSessionDetails(session.session_id);
                    }
                  }}
                >
                  <div className="session-user">
                    <strong>{session.user_name || 'Unknown'}</strong>
                    <span className="session-phone"> {session.user_phone}</span>
                  </div>
                  {session.native_name && (
                    <div className="session-card-native">Chart: {session.native_name}</div>
                  )}
                  {formatLlmLabel(session) && (
                    <div className="session-card-model" title="LLM used for the latest completed answer in this session">
                      Model: {formatLlmLabel(session)}
                    </div>
                  )}
                  <div className="session-date">{formatDate(session.created_at)}</div>
                  <div className="session-preview">{session.preview || 'Chat session'}</div>
                </div>
              ))
            )}
          </div>
        </aside>

        <div className="session-detail-pane">
          {selectedSession ? (
            <div className="session-details">
              <div className="session-header">
                <button
                  type="button"
                  className="session-back"
                  onClick={() => setSelectedSession(null)}
                  aria-label="Back to sessions list"
                >
                  <span className="session-back-icon" aria-hidden="true">
                    ←
                  </span>
                  <span className="session-back-label">Sessions</span>
                </button>
                <div className="session-header-center">
                  <h3 className="session-header-title">
                    <span className="session-header-title-text">Conversation</span>
                    {selectedSession.native_name && (
                      <span className="session-native-name">{selectedSession.native_name}</span>
                    )}
                  </h3>
                  {msgCount > 0 && (
                    <span className="session-msg-count">
                      {msgCount} message{msgCount === 1 ? '' : 's'}
                    </span>
                  )}
                  <div className="session-meta-chips">
                    {formatLlmLabel(selectedSession) && (
                      <span className="session-meta-chip" title="Provider and model ID from admin settings at answer time">
                        {formatLlmLabel(selectedSession)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.total_cost_inr_estimate === 'number' && (
                      <span
                        className="session-meta-chip session-meta-chip--accent"
                        title={selectedSession?.cost_summary?.note || 'Rough estimate'}
                      >
                        INR {selectedSession.cost_summary.total_cost_inr_estimate.toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.input_cost_non_cached_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Non-cached input cost estimate">
                        NC In INR {Number(selectedSession.cost_summary.input_cost_non_cached_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.input_cost_cached_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Cached input cost estimate">
                        C In INR {Number(selectedSession.cost_summary.input_cost_cached_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.cache_setup_cost_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Context cache setup input cost estimate">
                        Cache setup INR {Number(selectedSession.cost_summary.cache_setup_cost_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {typeof selectedSession?.cost_summary?.output_cost_inr_estimate === 'number' && (
                      <span className="session-meta-chip" title="Output token cost estimate">
                        Out INR {Number(selectedSession.cost_summary.output_cost_inr_estimate).toFixed(4)}
                      </span>
                    )}
                    {selectedSession?.cost_summary?.input_usd_per_1m != null && (
                      <span className="session-meta-chip" title="Input rate in USD per 1M tokens">
                        In ${Number(selectedSession.cost_summary.input_usd_per_1m || 0).toFixed(2)}/1M
                      </span>
                    )}
                    {selectedSession?.cost_summary?.output_usd_per_1m != null && (
                      <span className="session-meta-chip" title="Output rate in USD per 1M tokens">
                        Out ${Number(selectedSession.cost_summary.output_usd_per_1m || 0).toFixed(2)}/1M
                      </span>
                    )}
                    {selectedSession?.cost_summary?.pricing_tier && (
                      <span className="session-meta-chip" title="Pricing tier used for estimation">
                        {selectedSession.cost_summary.pricing_tier}
                      </span>
                    )}
                    {selectedSession?.cost_summary?.usd_to_inr_rate != null && (
                      <span className="session-meta-chip" title="USD to INR conversion rate">
                        USD/INR {Number(selectedSession.cost_summary.usd_to_inr_rate).toFixed(2)}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  className="session-close"
                  onClick={() => setSelectedSession(null)}
                  aria-label="Close conversation"
                >
                  <span aria-hidden="true">×</span>
                </button>
              </div>

              <div className="messages-container">
                {selectedSession.messages.map((message, index) => {
                  const parallelStages = Array.isArray(message.parallel_llm_usage?.stages)
                    ? message.parallel_llm_usage.stages
                    : [];
                  const hasParallelStages = parallelStages.length > 0;
                  const aggregatePromptChars = hasParallelStages
                    ? sumParallelStageField(parallelStages, 'input_chars')
                    : null;
                  const aggregateReplyChars = hasParallelStages
                    ? sumParallelStageField(parallelStages, 'output_chars')
                    : null;
                  const promptCharsForBadge =
                    aggregatePromptChars != null && aggregatePromptChars > 0
                      ? aggregatePromptChars
                      : Number(message.llm_prompt_chars) || 0;
                  const replyCharsForBadge =
                    aggregateReplyChars != null && aggregateReplyChars > 0
                      ? aggregateReplyChars
                      : Number(message.llm_response_chars) || 0;
                  const role =
                    message.sender === 'user'
                      ? 'user'
                      : message.sender === 'assistant'
                        ? 'assistant'
                        : 'assistant';
                  const answerModelLabel =
                    role === 'assistant' ? formatLlmLabel(selectedSession || {}) : null;
                  const label =
                    message.sender === 'user'
                      ? 'User'
                      : message.sender === 'assistant'
                        ? 'Assistant'
                        : String(message.sender || 'Message').replace(/^\w/, (c) => c.toUpperCase());
                  return (
                <div key={index} className={`message message--${role}`}>
                    <div className="message-label">
                      {label}
                    </div>
                    <div
                      className="message-content"
                      dangerouslySetInnerHTML={{ __html: formatMessageContent(message.content) }}
                    />
                    <div className="message-meta">
                      {answerModelLabel && (
                        <span
                          className="message-token-badge"
                          title="Provider and model used for this answer"
                        >
                          Model {answerModelLabel}
                        </span>
                      )}
                      {message.native_name && (
                        <span
                          className="message-native-badge"
                          title="Birth chart / Native"
                        >
                          {message.native_name}
                        </span>
                      )}
                      {Number.isFinite(promptCharsForBadge) && promptCharsForBadge > 0 && (
                        <span
                          className="message-char-badge message-char-badge--prompt"
                          title={
                            hasParallelStages
                              ? 'Total prompt characters for the parallel pipeline: sum of each LLM call prompt across all branches + merge (Σ Pr on stage rows).'
                              : message.sender === 'user'
                                ? 'Full prompt character count for the LLM call that answers this question (same as following assistant row)'
                                : 'Full prompt sent to the LLM (chart JSON + instructions + history + question)'
                          }
                        >
                          Prompt {Number(promptCharsForBadge).toLocaleString()} chars
                        </span>
                      )}
                      {message.sender === 'assistant' &&
                        Number.isFinite(replyCharsForBadge) &&
                        replyCharsForBadge > 0 && (
                          <span
                            className="message-char-badge message-char-badge--reply"
                            title={
                              hasParallelStages
                                ? 'Total raw output characters across all branch calls + merge (Σ Rp on stage rows).'
                                : 'Assistant reply text length after parsing (what the user sees)'
                            }
                          >
                            Reply {Number(replyCharsForBadge).toLocaleString()} chars
                          </span>
                        )}
                      {Number.isFinite(message.llm_input_tokens) && (
                        <span
                          className="message-token-badge"
                          title={
                            message.parallel_llm_usage?.stages?.length
                              ? 'Sum of billed input tokens across all parallel branch calls plus merge (Σ In on stage rows). Same as timing.parallel_llm_usage.totals.input_tokens when stored.'
                              : message.sender === 'user'
                                ? 'API usage: prompt tokens for the assistant reply after this question'
                                : 'API usage: prompt (input) tokens for this completion'
                          }
                        >
                          In {Number(message.llm_input_tokens).toLocaleString()}
                        </span>
                      )}
                      {Number.isFinite(message.llm_output_tokens) && (
                        <span
                          className="message-token-badge"
                          title={
                            message.parallel_llm_usage?.stages?.length
                              ? 'Sum of billed output tokens across all parallel branch calls plus merge (Σ Out on stage rows). Not the character length of the user-visible reply.'
                              : message.sender === 'user'
                                ? 'API usage: completion tokens for the assistant reply after this question'
                                : 'API usage: completion (output) tokens for this reply'
                          }
                        >
                          Out {Number(message.llm_output_tokens).toLocaleString()}
                        </span>
                      )}
                      {Number.isFinite(message.llm_cached_input_tokens) && (
                        <span className="message-token-badge" title="Provider-reported cached prompt tokens">
                          Cached {Number(message.llm_cached_input_tokens).toLocaleString()}
                        </span>
                      )}
                      {Number.isFinite(message.llm_non_cached_input_tokens) && (
                        <span className="message-token-badge" title="Provider-reported non-cached prompt tokens">
                          Non-cached {Number(message.llm_non_cached_input_tokens).toLocaleString()}
                        </span>
                      )}
                      {Number.isFinite(message.llm_cache_setup_input_tokens) &&
                        message.llm_cache_setup_input_tokens > 0 && (
                          <span
                            className="message-token-badge"
                            title="Estimated input tokens spent while creating Gemini context cache"
                          >
                            Cache setup {Number(message.llm_cache_setup_input_tokens).toLocaleString()}
                          </span>
                        )}
                      {typeof message?.cost_estimate?.cost_inr_estimate === 'number' && (
                        <span
                          className="message-cost-badge"
                          title={`Rough INR from pricing × ~${Number(message.cost_estimate?.tokens_estimate ?? 0).toLocaleString()} token estimate.${Number.isFinite(message.llm_input_tokens) ? ` API in ${Number(message.llm_input_tokens).toLocaleString()}.` : ''}${Number.isFinite(message.llm_output_tokens) ? ` API out ${Number(message.llm_output_tokens).toLocaleString()}.` : ''}${Number.isFinite(message.llm_prompt_chars) ? ` Prompt ${Number(message.llm_prompt_chars).toLocaleString()} chars.` : ''}`}
                        >
                          INR {message.cost_estimate.cost_inr_estimate.toFixed(4)}
                        </span>
                      )}
                      <span className="message-time">{formatTimeIST(message.timestamp)}</span>
                    </div>
                    {Array.isArray(message.parallel_llm_usage?.stages) &&
                      message.parallel_llm_usage.stages.length > 0 && (
                      <div
                        className="message-parallel-stages"
                        aria-label="Per-branch LLM usage (parallel chat)"
                      >
                        {(() => {
                          const stages = message.parallel_llm_usage.stages;
                          const blob = message.parallel_llm_usage.totals || {};
                          const sumPr = sumParallelStageField(stages, 'input_chars');
                          const sumRp = sumParallelStageField(stages, 'output_chars');
                          const sumIn = sumParallelStageField(stages, 'input_tokens');
                          const sumOut = sumParallelStageField(stages, 'output_tokens');
                          const sumCachedIn = sumParallelStageField(stages, 'cached_tokens');
                          const sumNonCachedIn = sumParallelStageField(stages, 'non_cached_input_tokens');
                          const sumSt = sumParallelStageField(stages, 'static_chars');
                          const sumDy = sumParallelStageField(stages, 'dynamic_chars');
                          const blobPr =
                            blob.input_chars != null ? Number(blob.input_chars) : null;
                          const blobIn =
                            blob.input_tokens != null ? Number(blob.input_tokens) : null;
                          const blobOut =
                            blob.output_tokens != null ? Number(blob.output_tokens) : null;
                          const promptBadge = message.llm_prompt_chars;
                          const inBadge = message.llm_input_tokens;
                          const outBadge = message.llm_output_tokens;
                          const stDyMismatch =
                            stages.length > 0 &&
                            sumSt > 0 &&
                            sumDy > 0 &&
                            sumSt + sumDy !== sumPr;
                          const warn =
                            stDyMismatch ||
                            (blobPr != null && blobPr !== sumPr) ||
                            (promptBadge != null &&
                              Number.isFinite(Number(promptBadge)) &&
                              Number(promptBadge) !== sumPr) ||
                            (blobIn != null && blobIn !== sumIn) ||
                            (inBadge != null &&
                              Number.isFinite(Number(inBadge)) &&
                              Number(inBadge) !== sumIn) ||
                            (blobOut != null && blobOut !== sumOut) ||
                            (outBadge != null &&
                              Number.isFinite(Number(outBadge)) &&
                              Number(outBadge) !== sumOut);
                          const title = [
                            'Σ = sum of all stage rows (7 branches + merge). Header Prompt/In/Out should match these sums.',
                            blobPr != null ? `totals.input_chars (stored)=${blobPr}` : null,
                            sumSt > 0 && sumDy > 0
                              ? `Σ St+Dy = ${(sumSt + sumDy).toLocaleString()} (should equal Σ Pr)`
                              : null,
                            stDyMismatch ? 'Σ St + Σ Dy ≠ Σ Pr — check static/dynamic split' : null,
                          ]
                            .filter(Boolean)
                            .join(' · ');
                          return (
                            <div
                              className={`message-parallel-sum${warn ? ' message-parallel-sum--warn' : ''}`}
                              title={title}
                            >
                              <span className="message-parallel-sum-label">Σ</span>
                              Pr {sumPr.toLocaleString()}c · Rp {sumRp.toLocaleString()}c · In{' '}
                              {sumIn.toLocaleString()} · Out {sumOut.toLocaleString()}
                              {' · '}CIn {sumCachedIn.toLocaleString()} · NCIn {sumNonCachedIn.toLocaleString()}
                              {sumSt > 0 && sumDy > 0 && (
                                <>
                                  {' '}
                                  · St {sumSt.toLocaleString()}c · Dy {sumDy.toLocaleString()}c
                                </>
                              )}
                              {warn && (
                                <span className="message-parallel-sum-warn" title="Mismatch detail">
                                  {' '}
                                  ⚠
                                </span>
                              )}
                            </div>
                          );
                        })()}
                        {message.parallel_llm_usage.stages.map((st, si) => {
                          const elapsedLabel = formatParallelElapsed(st.elapsed_ms);
                          const hasStDy =
                            st.static_chars != null &&
                            Number.isFinite(Number(st.static_chars)) &&
                            st.dynamic_chars != null &&
                            Number.isFinite(Number(st.dynamic_chars));
                          const titleParts = [
                            formatParallelStageLabel(st.stage),
                            elapsedLabel ? `time ${elapsedLabel}` : null,
                            hasStDy
                              ? `static ${Number(st.static_chars).toLocaleString()} chars · dynamic ${Number(
                                  st.dynamic_chars,
                                ).toLocaleString()} chars`
                              : null,
                            `prompt ${Number(st.input_chars || 0).toLocaleString()} chars · raw out ${Number(
                              st.output_chars || 0,
                            ).toLocaleString()} chars`,
                          ].filter(Boolean);
                          return (
                          <span
                            key={`${st.stage || 'stage'}-${si}`}
                            className="message-parallel-stage-pill"
                            title={titleParts.join(' — ')}
                          >
                            <span className="message-parallel-stage-name">
                              {formatParallelStageLabel(st.stage)}
                            </span>
                            {elapsedLabel && (
                              <span
                                className="message-parallel-chip message-parallel-chip--time"
                                title="LLM call duration (parallel branches: sum of attempts; merge: single synthesis call)"
                              >
                                {elapsedLabel}
                              </span>
                            )}
                            {hasStDy && (
                              <span
                                className="message-parallel-chip message-parallel-chip--static"
                                title="Static portion of the prompt (fixed instructions / role text)"
                              >
                                St {Number(st.static_chars).toLocaleString()}c
                              </span>
                            )}
                            {hasStDy && (
                              <span
                                className="message-parallel-chip message-parallel-chip--dynamic"
                                title="Dynamic portion (variable JSON, merge bundle, history slice, etc.)"
                              >
                                Dy {Number(st.dynamic_chars).toLocaleString()}c
                              </span>
                            )}
                            <span className="message-parallel-stage-tokens">
                              {' '}
                              In {Number(st.input_tokens || 0).toLocaleString()}
                              {' · '}
                              Out {Number(st.output_tokens || 0).toLocaleString()}
                              {' · '}
                              CIn {Number(st.cached_tokens || 0).toLocaleString()}
                              {' · '}
                              NCIn {Number(st.non_cached_input_tokens || 0).toLocaleString()}
                              {' · '}
                              Pr {Number(st.input_chars || 0).toLocaleString()}c
                              {' · '}
                              Rp {Number(st.output_chars || 0).toLocaleString()}c
                              {st.success === false ? ' ⚠' : ''}
                            </span>
                          </span>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="session-detail-empty">
              <div className="session-detail-empty-inner">
                <span className="session-detail-empty-icon" aria-hidden="true">
                  💬
                </span>
                <p className="session-detail-empty-title">Select a session</p>
                <p className="session-detail-empty-text">
                  Choose a conversation from the list to read the full thread. Assistant replies use
                  the full width for easier reading.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminChatHistory;