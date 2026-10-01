import click
import httpx
import time
from typing import List
from .spec import Spec
from ._config import Config
from .utils._cacheir import save_cache

@click.command()
@click.argument('spec_links', nargs=-1, required=True)
@click.option('--timeout', default=Config.GET_SPEC_TIMEOUT, help='Timeout for downloading specs in seconds')
@click.option('--cache-processed',
              default=Config.CACHE_AS_PROCESSED_SCHEMAS,
              help='Convert specifications into schemas and cache them that way')
def cache_specs(spec_links: List[str], timeout: int, cache_processed: bool) -> None:
    """
    Pre-downloads and caches specifications from provided URLs.
    
    SPEC_LINKS: One or more specification URLs to cache
    """
    start_time = time.time()
    click.echo(f"Starting caching of {len(spec_links)} specifications...")
    
    for spec_link in spec_links:
        spec_start_time = time.time()
        try:
            click.echo(f"\nProcessing {spec_link}...")
            spec = Spec(spec_link=spec_link, func_name="cache_specs", cache_processed=cache_processed)
            spec.get_prepared_spec_units()
            spec_time = time.time() - spec_start_time
            click.echo(f"✅ Specification successfully cached: {spec_link} (took {spec_time:.2f}s)")
            
        except Exception as e:
            spec_time = time.time() - spec_start_time
            click.echo(f"❌ Error processing {spec_link}: {str(e)} (took {spec_time:.2f}s)")
    
    total_time = time.time() - start_time
    click.echo(f"\nCaching completed! Total time: {total_time:.2f}s")

if __name__ == '__main__':
    cache_specs() 
    