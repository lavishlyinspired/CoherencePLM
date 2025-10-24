import neo4j, { Driver, RecordShape } from "neo4j-driver";
import { URI, USER, PASSWORD, DATABASE } from "./creds";
import { Node, nvlResultTransformer, Relationship } from "@neo4j-nvl/base";

export const connect = async (
  query: string,
  param = {}
): Promise<
  | {
      recordObjectMap: Map<string, RecordShape>;
      nodes: Node[];
      relationships: Relationship[];
      rawRecords?: any[]; // Add raw records for queries that need actual data
    }
  | undefined
> => {
  try {
    const driver: Driver = neo4j.driver(URI, neo4j.auth.basic(USER, PASSWORD));

    const result = await driver.executeQuery(query, param, {
      database: DATABASE,
      resultTransformer: nvlResultTransformer,
    });

    // For queries that need the actual data (like neighbors), we need to run a separate query
    // to get the raw records since nvlResultTransformer strips away relationship types
    if (query.includes('MATCH (n)-[r]-(neighbor)') || query.includes('MATCH (n)-[r]-(other)')) {
      const session = driver.session({ database: DATABASE });
      try {
        const rawResult = await session.run(query, param);
        const rawRecords = rawResult.records.map(record => record.toObject());
        
        // Merge raw records into the result
        return {
          ...result,
          rawRecords
        };
      } finally {
        await session.close();
      }
    }

    return result;
  } catch (err) {
    console.error(`Connection error\n${err}.`);
  }
};