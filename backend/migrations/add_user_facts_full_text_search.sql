CREATE INDEX IF NOT EXISTS idx_user_facts_search ON user_facts USING GIN
((to_tsvector('english', COALESCE(fact, '') || ' ' || COALESCE(category, '')) ||
  to_tsvector('simple', COALESCE(fact, '') || ' ' || COALESCE(category, ''))));
