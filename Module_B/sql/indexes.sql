-- Add indexes based on API query patterns.
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_email ON portfolios(email);
CREATE INDEX IF NOT EXISTS idx_portfolios_updated_at ON portfolios(updated_at);
CREATE INDEX IF NOT EXISTS idx_member_group_map_group_user ON member_group_map(group_id, user_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
