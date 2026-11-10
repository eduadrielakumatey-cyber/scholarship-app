// src/pages/Detail.jsx
//
// Full detail view for a single scholarship, reached by tapping a title
// in the Saved list. Shows the same scored metrics as the swipe card plus
// the full description and a link to the original source.

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import * as api from "../api/client.js";
import ScholarshipMetrics from "../components/ScholarshipMetrics.jsx";

export default function Detail() {
  const { id } = useParams();
  const [scholarship, setScholarship] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getScholarship(id).then(setScholarship).catch((err) => setError(err.message));
  }, [id]);

  if (error) return <div className="screen"><p className="error-text">{error}</p></div>;
  if (!scholarship) return <div className="screen"><p className="page-subtitle">Loading...</p></div>;

  return (
    <div className="screen">
      <Link to="/saved" className="text-link-button">
        ← Back to saved
      </Link>
      <h1 className="page-title" style={{ marginTop: 12 }}>
        {scholarship.title}
      </h1>
      <p className="page-subtitle">{scholarship.organization}</p>

      <div style={{ borderRadius: 16, overflow: "hidden", marginBottom: 20 }}>
        <ScholarshipMetrics scholarship={scholarship} />
      </div>

      <p style={{ lineHeight: 1.6 }}>{scholarship.description}</p>

      <Link className="primary-button" style={{ display: "block", textAlign: "center", marginTop: 20 }}
            to={`/apply/${scholarship.id}`}>
        {scholarship.hosted ? "Apply in ScholarMatch" : "Apply"}
      </Link>
    </div>
  );
}
